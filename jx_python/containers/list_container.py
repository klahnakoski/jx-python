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

from jx_base.expressions import TRUE
from jx_base.expressions._utils import jx_expression
from jx_base.expressions.variable import is_variable
from jx_base.language import is_expression, ID
from jx_base.meta_columns import get_schema_from_jx_type, get_schema_from_list
from jx_base.models.container import Container
from jx_base.models.namespace import Namespace
from jx_base.models.schema import Schema
from jx_base.models.snowflake import Snowflake
from jx_base.models.table import Table
from jx_base.utils import delist, enlist
from jx_python.containers.lists.aggs import is_aggs, list_aggs
from jx_python.convert import list2cube, list2table
from jx_python.expressions import jx_expression_to_function
from mo_collections import UniqueIndex
from mo_dots import (
    Data,
    Null,
    is_data,
    is_list,
    from_data,
    to_data,
    dict_to_data,
    last,
    startswith_field, coalesce, register_many,
)
from mo_future import first, sort_using_key
from mo_imports import export, expect
from mo_json import JX_IS_NULL, value_to_jx_type, JxType, to_jx_type, union_type, array_of
from mo_logs import logger
from mo_threads import Lock

jx = expect("jx")


class ListContainer(Container, Namespace, Table):
    """
    A CONTAINER WITH ONLY ONE TABLE
    A PYTHON LIST PAIRED WITH SCHEMA SO QUERY EXPRESSIONS CAN BE TRANSPILED
    """

    def __init__(self, name, data, schema=None):
        # TODO: STORE THIS LIKE A CUBE FOR FASTER ACCESS AND TRANSFORMATION
        Container.__init__(self)
        self.name = name = coalesce(name, ".")
        self.data = data = list(from_data(data))
        self.container = self
        self.schema = schema or get_schema_from_list(name, data)
        self.locker = Lock()  # JUST IN CASE YOU WANT TO DO MORE THAN ONE THING
        setattr(self, ID, -1)

    @property
    def nested_path(self):
        return [self.name]

    @property
    def jx_type(self):
        return self.name + array_of(union_type(*(
            col.name + to_jx_type(col.json_type)
            for col in self.schema.columns
        )))

    def __call__(self, row=None, rownum=None, rows=None):
        return self

    def get_facts(self, fact_name):
        return self

    def get_schema(self, query_path=None):
        if query_path is None:
            return self.schema
        snowflake = self.schema.snowflake
        if query_path not in snowflake.query_paths:
            logger.error("This container only has tables with names {names}", names=self.schema.snowflake.query_paths)

        nested_path = []
        for path in snowflake.query_paths:
            if startswith_field(query_path, path):
                nested_path.append(path)
        return Schema(list(reversed(nested_path)), snowflake)

    def get_snowflake(self, fact_name):
        return Snowflake(fact_name, self)

    def get_relations(self):
        return self.relations[:]

    def get_columns(self, table_name):
        return self.columns.find_columns(table_name)

    def get_tables(self):
        return list(sorted(self.columns.data.keys()))

    @property
    def namespace(self):
        return self

    def last(self):
        """
        :return:  Last element in the list, or Null
        """
        last(self.data)

    def query(self, query: "QueryOp"):
        query = to_data(query)
        output = self
        if is_aggs(query):
            output = list_aggs(output.data, query)
        else:
            if query.where is not TRUE:
                output = output.where(query.where)

            if query.sort:
                output = output.sort(query.sort)

            if query.select:
                output = output.select(query.select)

        # TODO: ADD EXTRA COLUMN DESCRIPTIONS TO RESULTING SCHEMA
        for param in query.window:
            output.window(param)

        if query.format:
            if query.format == "list":
                return Data(data=output.data, meta={"format": "list"})
            elif query.format == "table":
                head = [c.name for c in output.schema.snowflake.columns]
                data = [[r if h == "." else r[h] for h in head] for r in output.data]
                return Data(header=head, data=data, meta={"format": "table"})
            elif query.format == "cube":
                head = [c.name for c in output.schema.snowflake.columns]
                rows = [[r[h] for h in head] for r in output.data]
                data = {h: c for h, c in zip(head, zip(*rows))}
                return Data(
                    data=data,
                    meta={"format": "cube"},
                    edges=[{
                        "name": "rownum",
                        "domain": {"type": "rownum", "min": 0, "max": len(rows), "interval": 1},
                    }],
                )
            else:
                logger.error("unknown format {format}", format=query.format)
        else:
            return output

    def update(self, command):
        """
        EXPECTING command == {"set":term, "clear":term, "where":where}
        THE set CLAUSE IS A DICT MAPPING NAMES TO VALUES
        THE where CLAUSE IS A JSON EXPRESSION FILTER
        """
        command = to_data(command)
        command_clear = enlist(command["clear"])
        command_set = command.set.items()
        command_where = jx.get(command.where)

        for c in self.data:
            if command_where(c):
                for k in command_clear:
                    c[k] = None
                for k, v in command_set:
                    c[k] = v

    def where(self, where):
        if is_data(where) or is_expression(where):
            temp = jx_expression_to_function(where)
        else:
            temp = where

        return ListContainer("from " + self.name, filter(temp, self.data), self.schema)

    filter = where

    def sort(self, sort):
        return ListContainer("sorted " + self.name, jx.sort(self.data, sort, already_normalized=True), self.schema,)

    def get(self, select):
        """
        :param select: the variable to extract from list
        :return:  a simple list of the extraction
        """
        if is_list(select):
            return [(d[s] for s in select) for d in self.data]
        else:
            return [d[select] for d in self.data]

    def select(self, select):
        selects = select.terms
        if (
            len(selects) == 1
            and is_variable(selects[0].value)
            and selects[0].value.var == "."
            and selects[0].name == "."
        ):
            return self

        exprs = [jx_expression(s.value) for s in selects]
        jx_type = JX_IS_NULL
        new_data = []
        for row in self.data:
            result = Data()
            for s, e in zip(selects, exprs):
                value = e(row)
                result[s.name] = e(row)
                jx_type = jx_type | s.name + value_to_jx_type(value)
            new_data.append(from_data(result))

        new_name = f"from {self.name}"
        new_schema = get_schema_from_jx_type(new_name, jx_type)
        return ListContainer(new_name, data=new_data, schema=new_schema)

    def window(self, window):
        # _ = window
        jx.window(self.data, window)
        return self

    def format(self, format):
        if format == "table":
            frum = list2table(self.data, self._schema.lookup.keys())
        elif format == "cube":
            frum = list2cube(self.data, self.schema.lookup.keys())
        else:
            frum = self.__data__()

        return frum

    def groupby(self, keys, contiguous=False):
        try:
            keys = enlist(keys)
            get_key = jx_expression_to_function(keys)
            if not contiguous:
                data = sort_using_key(self.data, key=get_key)

            def _output():
                for g, v in itertools.groupby(data, get_key):
                    group = Data()
                    for k, gg in zip(keys, g):
                        group[k] = gg
                    yield (group, to_data(list(v)))

            return _output()
        except Exception as e:
            logger.error("Problem grouping", e)

    def insert(self, documents):
        self.data.extend(documents)

    def extend(self, documents):
        self.data.extend(documents)

    def __data__(self):
        if first(self.schema.columns).name == ".":
            return dict_to_data({"meta": {"format": "list"}, "data": self.data})
        else:
            return dict_to_data({
                "meta": {"format": "list"},
                "data": [{k: delist(v) for k, v in row.items()} for row in self.data],
            })

    def get_columns(self, table_name=None):
        return self.schema.values()

    def add(self, value):
        self.data.append(value)

    def __getitem__(self, item):
        if item < 0 or len(self.data) <= item:
            return Null
        return self.data[item]

    def __iter__(self):
        return (to_data(d) for d in self.data)

    def __len__(self):
        return len(self.data)

    def get_snowflake(self, name):
        if self.name != name:
            logger.error("This container only has table by name of {name}", name=name)
        return self

    def get_table(self, name):
        if self is name or self.name == name:
            return self
        logger.error("This container only has table by name of {name}", name=name)


DUAL = ListContainer(
    name="dual", data=[{}], schema=Schema(["dual"], Snowflake(None, ["dual"], columns=UniqueIndex(keys=("name",))))
)

register_many(ListContainer)

export("jx_base.models.container", ListContainer)
