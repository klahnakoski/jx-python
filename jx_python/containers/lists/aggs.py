# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import itertools
from functools import cmp_to_key

from jx_base.domains import DefaultDomain, SimpleSetDomain
from jx_base.expressions.literal import Literal, NULL
from jx_base.expressions.product_op import ProductOp
from jx_base.expressions.sum_op import SumOp
from jx_base.language import is_op, value_compare
from jx_python.expressions import jx_expression_to_function
from mo_collections.tensor import Tensor
from mo_dots import Data, Null, exists, to_data
from jx_base.utils import coalesce, delist, is_true
from mo_future import first
from mo_json import value2json
from mo_logs import Log
from mo_math import UNION
from mo_times.dates import Date

_ = Date


def is_aggs(query):
    if query.edges or query.groupby or any(s.aggregate is not NULL for s in query.select.terms):
        return True
    return False


def list_aggs(frum, query):
    """
    THE edges PATH: THE CUBE IS THE WORKING STRUCTURE.  A Tensor IS DENSE BY CONSTRUCTION, SO
    EVERY COORDINATE EXISTS (WITH ITS OWN list OF VALUES) BEFORE ANY DATA ARRIVES; ONE PASS
    DROPS EACH ROW'S VALUE INTO THE CELLS IT BELONGS TO, THEN EACH CELL IS AGGREGATED IN PLACE.
    """
    frum = to_data(frum)
    if query.groupby:
        return groupby_aggs(frum, query)

    edges = _resolve_domains(frum, query.edges, query.limit)
    terms = query.select.terms
    dims = [len(e.domain.partitions) + (1 if e.allowNulls else 0) for e in edges]

    s_accessors = [(t.name, jx_expression_to_function(t.value)) for t in terms]
    result = {t.name: Tensor(dims=dims, zeros=list) for t in terms}
    where = jx_expression_to_function(query.where)
    coord = [None] * len(edges)
    edge_accessor = [(i, make_accessor(e)) for i, e in enumerate(edges)]

    net_new_edge_names = set(to_data(edges).name) - UNION(e.value.vars() for e in edges)
    if net_new_edge_names & UNION(t.value.vars() for t in terms):
        # s_accessor NEEDS THESE EDGES, SO WE PASS THEM ANYWAY
        for d in filter(where, frum):
            d = d.copy()
            for c, get_matches in edge_accessor:
                coord[c] = get_matches(d)

            for s_name, s_accessor in s_accessors:
                mat = result[s_name]
                for c in itertools.product(*coord):
                    for e, cc in zip(edges, c):
                        d[e.name] = e.domain.getKeyByIndex(cc)
                    mat[c].append(s_accessor(d, c, frum))
    else:
        # FASTER
        for d in filter(where, frum):
            for c, get_matches in edge_accessor:
                coord[c] = get_matches(d)

            for s_name, s_accessor in s_accessors:
                mat = result[s_name]
                for c in itertools.product(*coord):
                    mat[c].append(s_accessor(d, c, frum))

    for t in terms:
        m = result[t.name]
        for c, values in m.items():
            m[c] = _aggregate(t, values)

    return _cube_to_rows(query, edges, terms, result, dims)


def _resolve_domains(frum, edges, query_limit):
    """
    INFER A DOMAIN FOR EVERY DefaultDomain EDGE.  RETURN A NEW EDGE LIST; THE QUERY'S OWN EDGES
    ARE LEFT ALONE (THE SAME QueryOp MAY BE RUN OVER OTHER DATA)
    """
    output = []
    for e in edges:
        if not isinstance(e.domain, DefaultDomain):
            output.append(e)
            continue
        accessor = jx_expression_to_function(e.value)
        unique_values = set(map(accessor, frum))
        e = e.copy()
        if None in unique_values:
            e.allowNulls = coalesce(e.allowNulls, True)
            unique_values -= {None}
        # value_compare, NOT sorted(): THE VALUES CAN BE MIXED-TYPE, OR TUPLES HOLDING A NULL
        parts = sorted(unique_values, key=cmp_to_key(value_compare))
        # A DOMAIN WRITTEN OUT AS `{"type": "default"}` LOSES THE QUERY'S limit ON THE WAY
        # THROUGH _normalize_edge, WHICH ONLY FORWARDS IT FOR A BARE `edges: ["name"]`
        limit = coalesce(e.domain.limit(), query_limit())
        if exists(limit) and len(parts) > limit:
            # A TRUNCATED DOMAIN LEAVES VALUES OUTSIDE IT, WHICH LAND IN THE allowNulls PART
            parts = parts[:limit]
            e.allowNulls = True
        e.domain = SimpleSetDomain(partitions=parts)
        output.append(e)
    return output


def _cube_to_rows(query, edges, terms, result, dims):
    """
    ONE ROW PER COORDINATE OF THE DENSE CUBE - EMPTY CELLS INCLUDED - IN CUBE ORDER (WHICH IS
    DOMAIN ORDER, WITH THE allowNulls PART LAST)
    """
    # ANY TERM'S MATRIX ENUMERATES THE COORDINATE SPACE; `select: []` HAS NONE, SO MAKE ONE
    anchor = result[terms[0].name] if terms else Tensor(dims=dims)

    output = []
    for c, _ in anchor.items():
        values = [(e.name, e.domain.getKeyByIndex(cc)) for e, cc in zip(edges, c)]
        values.extend((t.name, result[t.name][c]) for t in terms)
        if len(values) == 1 and values[0][0] == ".":
            # NAMED dot, AND NOTHING ELSE: THE ROW *IS* THE VALUE, NOT A PROPERTY OF ONE
            output.append(values[0][1])
            continue
        record = Data()
        for name, value in values:
            record[name] = value
        output.append(record)

    from jx_python.containers.list_container import ListContainer

    return ListContainer("from " + query.frum.name, output)


def groupby_aggs(frum, query):
    """
    GROUP THE ROWS, THEN RUN EACH select TERM'S AGGREGATE OVER THE VALUES OF ITS
    GROUP.  RETURNS ROWS (list FORMAT); THE edges/cube PATH IS SEPARATE (list_aggs)
    """
    where = jx_expression_to_function(query.where)
    accessors = [(g.name, jx_expression_to_function(g.value)) for g in query.groupby]
    terms = [(t, jx_expression_to_function(t.value)) for t in query.select.terms]

    groups = {}  # KEY (AS json) -> (KEY VALUES, ROWS)
    for row in frum:
        if not is_true(where(row)):
            continue
        keys = [accessor(row) for _, accessor in accessors]
        _, rows = groups.setdefault(value2json(keys), (keys, []))
        rows.append(row)

    output = []
    for keys, rows in groups.values():
        record = Data()
        for (name, _), key in zip(accessors, keys):
            record[name] = key
        for name, value in _aggregate_group(terms, rows).items():
            record[name] = value
        output.append(record)

    from jx_python.containers.list_container import ListContainer

    return ListContainer("from " + query.frum.name, output)


def value_aggs(frum, query):
    """
    AGGREGATES WITHOUT edges/groupby ARE ONE GROUP: RETURN THE VALUE ITSELF (A LONE,
    UNNAMED select CLAUSE) OR AN OBJECT OF THE NAMED AGGREGATES
    """
    where = jx_expression_to_function(query.where)
    terms = [(t, jx_expression_to_function(t.value)) for t in query.select.terms]
    rows = [row for row in frum if is_true(where(row))]

    acc = _aggregate_group(terms, rows)
    if len(terms) == 1 and terms[0][0].name == ".":
        return first(acc.values())
    record = Data()
    for name, value in acc.items():
        record[name] = value
    return record


def _aggregate_group(terms, rows):
    """RUN EACH select TERM'S AGGREGATE OVER THE ROWS OF ONE GROUP"""
    return {term.name: _aggregate(term, [accessor(row) for row in rows]) for term, accessor in terms}


def _aggregate(term, values):
    """COLLAPSE ONE select TERM'S COLLECTION OF VALUES TO THE ONE VALUE IT REPORTS"""
    if term.aggregate is NULL:
        # NOT AN AGGREGATE: EVERY ROW OF THE GROUP HAS THE SAME VALUE
        return delist(values[:1])
    if not any(exists(v) for v in values):
        if term.default is not NULL:
            return term.default(None)
        if any(is_op(term.aggregate, op) for op in (SumOp, ProductOp)):
            # AN AGGREGATE IS A DECLARATION OVER A GROUP, NOT AN EXPRESSION OVER ONE DOCUMENT:
            # AN EMPTY GROUP HAS NOTHING TO REPORT, EVEN WHERE THE DECISIVE OPERATOR IS TOTAL
            # (sum OF NOTHING IS 0 - SEE test_edge_2.test_sum_rows).  THE COUNTING AGGREGATES
            # ARE NOT LISTED: count/cardinality OF AN EMPTY GROUP REALLY IS 0
            return Null
    return term.aggregate.__class__(frum=Literal(values))(None)


def make_accessor(e):
    d = e.domain
    # d = _normalize_domain(d)
    if d.partitions and all(exists(p.where) for p in d.partitions):
        # THE PARTITIONS CARRY THEIR OWN FILTERS, AND THEY ARE A case: THE FIRST ONE A ROW
        # MATCHES CLAIMS IT (SEE test_edge_1.test_edge_w_partition_filters), OR NONE DO
        filters = [(p.dataIndex, jx_expression_to_function(p.where)) for p in d.partitions]

        def output0(row):
            for i, f in filters:
                if is_true(f(row)):
                    return [i]
            if e.allowNulls:
                return [len(d.partitions)]
            return []

        return output0
    elif e.value:
        accessor = jx_expression_to_function(e.value)
        if e.allowNulls:

            def output1(row):
                return [d.getIndexByKey(accessor(row))]

            return output1
        else:

            def output2(row):
                c = d.getIndexByKey(accessor(row))
                if c == len(d.partitions):
                    return []
                else:
                    return [c]

            return output2
    elif e.range:
        for p in d.partitions:
            if p["max"] == None or p["min"] == None:
                Log.error("Inclusive expects domain parts to have `min` and `max` properties")

        mi_accessor = jx_expression_to_function(e.range.min)
        ma_accessor = jx_expression_to_function(e.range.max)

        if e.range.mode == "inclusive":

            def output3(row):
                mi, ma = mi_accessor(row), ma_accessor(row)
                output = [p.dataIndex for p in d.partitions if mi <= p["max"] and p["min"] < ma]
                if e.allowNulls and not output:
                    return [len(d.partitions)]  # ENSURE THIS IS NULL
                return output

            return output3
        else:

            def output4(row):
                mi, ma = mi_accessor(row), ma_accessor(row)
                var = d.key
                output = [p.dataIndex for p in d.partitions if mi <= p[var] < ma]
                if e.allowNulls and not output:
                    return [len(d.partitions)]  # ENSURE THIS IS NULL
                return output

            return output4
