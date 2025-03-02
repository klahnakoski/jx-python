# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from copy import copy
from importlib import import_module

import mo_math
from jx_base.expressions._utils import jx_expression
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.filter_op import _normalize_where
from jx_base.expressions.select_op import SelectOp, _normalize_selects, SelectOne, normalize_one
from jx_base.expressions.variable import Variable
from jx_base.expressions.sort_op import _normalize_sort
from jx_base.language import is_expression, is_op
from jx_base.models.dimensions import Dimension
from jx_base.utils import is_variable_name, coalesce, delist, enlist
from mo_dots import *
from mo_future import is_text
from mo_imports import expect
from mo_imports import export
from mo_logs import Log
from mo_math import AND, UNION

Column = expect("Column")

BAD_SELECT = "Expecting `value` or `aggregate` in select clause not {{select}}"
DEFAULT_LIMIT = 10
MAX_LIMIT = 10000
DEFAULT_SELECT = (SelectOne(".", Variable(".")),)


class QueryOp(Expression):
    __slots__ = [
        "frum",
        "chunk_size",
        "destination",
    ]

    def __init__(
            self,
            frum,
            chunk_size=None,
            destination=None,
    ):
        Expression.__init__(self, None)
        self.frum = frum
        self.chunk_size = chunk_size
        self.destination = destination

    @classmethod
    def define(cls, expr):
        return jx_expression(expr, cls.lang)

    def __data__(self):
        return self.frum.__data__()

    def copy(self):
        return QueryOp(frum=copy(self.frum), chunk_size=self.chunk_size, destination=self.destination)

    def vars(self):
        """
        :return: variables in query
        """
        return self.frum.vars()

    def map(self, map_):
        return QueryOp(frum=self.frum.map(map_))

    def missing(self, lang):
        return FALSE

    @property
    def columns(self):
        return enlist(self.select) + coalesce(self.edges, self.groupby)

    @property
    def query_path(self):
        return self.frum.schema.query_path

    @property
    def column_names(self):
        return enlist(self.select).name + self.edges.name + self.groupby.name

    def __getitem__(self, item):
        if item == "from":
            return self.frum
        return Data.__getitem__(self, item)

    def copy(self):
        output = object.__new__(QueryOp)
        for s in QueryOp.__slots__:
            setattr(output, s, getattr(self, s))
        return output

    def __data__(self):
        output = dict_to_data({s: getattr(self, s) for s in QueryOp.__slots__})
        return output


def temper_limit(limit, query):
    return coalesce(query.limit, 10)


def _import_temper_limit():
    global temper_limit
    try:
        temper_limit = import_module("jx_elasticsearch.es52").temper_limit
    except Exception as e:
        pass


def _map_term_using_schema(master, path, term, schema_edges):
    """
    IF THE WHERE CLAUSE REFERS TO FIELDS IN THE SCHEMA, THEN EXPAND THEM
    """
    output = FlatList()
    for k, v in term.items():
        dimension = schema_edges[k]
        if isinstance(dimension, Dimension):
            domain = dimension.getDomain()
            if dimension.fields:
                if is_data(dimension.fields):
                    # EXPECTING A TUPLE
                    for local_field, es_field in dimension.fields.items():
                        local_value = v[local_field]
                        if local_value == None:
                            output.append({"missing": {"field": es_field}})
                        else:
                            output.append({"term": {es_field: local_value}})
                    continue

                if len(dimension.fields) == 1 and is_variable_name(dimension.fields[0]):
                    # SIMPLE SINGLE-VALUED FIELD
                    if domain.getPartByKey(v) is domain.NULL:
                        output.append({"missing": {"field": dimension.fields[0]}})
                    else:
                        output.append({"term": {dimension.fields[0]: v}})
                    continue

                if AND(is_variable_name(f) for f in dimension.fields):
                    # EXPECTING A TUPLE
                    if not isinstance(v, tuple):
                        Log.error("expecing {name}={value} to be a tuple", name=k, value=v)
                    for i, f in enumerate(dimension.fields):
                        vv = v[i]
                        if vv == None:
                            output.append({"missing": {"field": f}})
                        else:
                            output.append({"term": {f: vv}})
                    continue
            if len(dimension.fields) == 1 and is_variable_name(dimension.fields[0]):
                if domain.getPartByKey(v) is domain.NULL:
                    output.append({"missing": {"field": dimension.fields[0]}})
                else:
                    output.append({"term": {dimension.fields[0]: v}})
                continue
            if domain.partitions:
                part = domain.getPartByKey(v)
                if part is domain.NULL or not part.esfilter:
                    Log.error("not expected to get NULL")
                output.append(part.esfilter)
                continue
            else:
                Log.error("not expected")
        elif is_data(v):
            sub = _map_term_using_schema(master, path + [k], v, schema_edges[k])
            output.append(sub)
            continue

        output.append({"term": {k: v}})
    return {"and": output}


def _where_terms(master, where, schema):
    """
    USE THE SCHEMA TO CONVERT DIMENSION NAMES TO ES FILTERS
    master - TOP LEVEL WHERE (FOR PLACING NESTED FILTERS)
    """
    if is_data(where):
        if where.term:
            # MAP TERM
            try:
                output = _map_term_using_schema(master, [], where.term, schema.edges)
                return output
            except Exception as e:
                Log.error("programmer problem?", e)
        elif where.terms:
            # MAP TERM
            output = FlatList()
            for k, v in where.terms.items():
                if not is_container(v):
                    Log.error("terms filter expects list of values")
                edge = schema.edges[k]
                if not edge:
                    output.append({"terms": {k: v}})
                else:
                    if is_text(edge):
                        # DIRECT FIELD REFERENCE
                        return {"terms": {edge: v}}
                    try:
                        domain = edge.getDomain()
                    except Exception as e:
                        Log.error("programmer error", e)
                    fields = domain.dimension.fields
                    if is_data(fields):
                        or_agg = []
                        for vv in v:
                            and_agg = []
                            for local_field, es_field in fields.items():
                                vvv = vv[local_field]
                                if vvv != None:
                                    and_agg.append({"term": {es_field: vvv}})
                            or_agg.append({"and": and_agg})
                        output.append({"or": or_agg})
                    elif is_list(fields) and len(fields) == 1 and is_variable_name(fields[0]):
                        output.append({"terms": {fields[0]: v}})
                    elif domain.partitions:
                        output.append({"or": [domain.getPartByKey(vv).esfilter for vv in v]})
            return {"and": output}
        elif where["or"]:
            return {"or": [from_data(_where_terms(master, vv, schema)) for vv in where["or"]]}
        elif where["and"]:
            return {"and": [from_data(_where_terms(master, vv, schema)) for vv in where["and"]]}
        elif where["not"]:
            return {"not": from_data(_where_terms(master, where["not"], schema))}
    return where


export("jx_base.expressions.variable", QueryOp)
export("jx_base.models.container", QueryOp)
