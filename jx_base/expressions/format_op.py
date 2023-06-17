# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import jx_expression
from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import Literal, is_literal
from jx_base.models.container import Container
from jx_base.utils import enlist, delist
from mo_collections.matrix import Matrix
from mo_dots import is_list, from_data, Data
from mo_json.typed_encoder import ARRAY_KEY
from mo_json.types import JX_TEXT, JX_ANY, JxType
from mo_logs import Log


class FormatOp(Expression):
    def __init__(self, frum, format):
        Expression.__init__(self, frum, format)
        if not is_literal(format):
            logger.error("Expecting literal format")
        self.frum, self.format = frum, format

    @classmethod
    def define(cls, expr):
        frum, format = expr['format']
        return FormatOp(jx_expression(frum), Literal(format))

    def __data__(self):
        return {"format": [self.frum.__data__(), self.format]}

    def vars(self):
        return self.frum.vars() | self.format.vars()

    def map(self, map_):
        return FormatOp(self.frum.map(map_), self.format.map(map_))

    @property
    def type(self):
        if self.format == "value":
            return self.frum.type[ARRAY_KEY]
        elif self.format == "list":
            return self.frum.type
        elif self.format == "cube":
            # TODO: WHAT IS THE CUBE TYPE?
            head = [c.name for c in self.frum.schema.columns]
            return JxType(
                data={h: {ARRAY_KEY: {ARRAY_KEY: JX_ANY}} for h in head},
                meta={"format": JX_TEXT},
                edges={ARRAY_KEY: {"name": JX_TEXT, "domain": JX_ANY}},
            )

    def apply(self, container: Container):
        format = self.format.value

        result = self.frum.apply(container)
        sql = result.to_sql(container.namespace)
        if format == "sql":
            return sql

        # we are expecting a deep query format and deep query result
        result = container.query(sql)

        # DID NOT THINK THIS FAR YET
        if format == "container":
            output = QueryTable(new_table, container=container)
        elif format == "cube" or (not format and normalized_query.edges):
            column_names = [None] * (max(c.push_column_index for c in index_to_columns.values()) + 1)
            for c in index_to_columns.values():
                column_names[c.push_column_index] = c.push_column_name

            if len(normalized_query.edges) == 0 and len(normalized_query.groupby) == 0:
                data = {n: Data() for n in column_names}
                for s in index_to_columns.values():
                    data[s.push_list_name][s.push_column_child] = from_data(s.pull(result.data[0]))
                if is_list(normalized_query.select):
                    select = [{"name": s.name} for s in normalized_query.select]
                else:
                    select = {"name": normalized_query.select.name}

                return Data(data=from_data(data), select=select, meta={"format": "cube"})

            if not result.data:
                edges = []
                dims = []
                for i, e in enumerate(normalized_query.edges + normalized_query.groupby):
                    allowNulls = coalesce(e.allowNulls, True)

                    if e.domain.type == "set" and e.domain.partitions:
                        domain = SimpleSetDomain(partitions=e.domain.partitions.name)
                    elif e.domain.type == "range":
                        domain = e.domain
                    elif is_op(e.value, TupleOp):
                        pulls = (
                            jx
                            .sort(
                                [c for c in index_to_columns.values() if c.push_list_name == e.name],
                                "push_column_child",
                            )
                            .pull
                        )
                        parts = [tuple(p(d) for p in pulls) for d in result.data]
                        domain = SimpleSetDomain(partitions=jx.sort(set(parts)))
                    else:
                        domain = SimpleSetDomain(partitions=[])

                    dims.append(1 if allowNulls else 0)
                    edges.append(Data(name=e.name, allowNulls=allowNulls, domain=domain))

                data = {}
                for si, s in enumerate(enlist(normalized_query.select)):
                    if s.aggregate == "count":
                        data[s.name] = Matrix(dims=dims, zeros=0)
                    else:
                        data[s.name] = Matrix(dims=dims)

                if is_list(normalized_query.select):
                    select = [{"name": s.name} for s in normalized_query.select]
                else:
                    select = {"name": normalized_query.select.name}

                return Data(
                    meta={"format": "cube"}, edges=edges, select=select, data={k: v.cube for k, v in data.items()},
                )

            columns = None

            edges = []
            dims = []
            for g in normalized_query.groupby:
                g.is_groupby = True

            for i, e in enumerate(normalized_query.edges + normalized_query.groupby):
                allowNulls = coalesce(e.allowNulls, True)

                if e.domain.type == "set" and e.domain.partitions:
                    domain = e.domain
                elif e.domain.type == "range":
                    domain = e.domain
                elif e.domain.type == "time":
                    domain = wrap(mo_json.scrub(e.domain))
                elif e.domain.type == "duration":
                    domain = to_data(mo_json.scrub(e.domain))
                elif is_op(e.value, TupleOp):
                    pulls = (
                        jx
                        .sort(
                            [c for c in index_to_columns.values() if c.push_list_name == e.name], "push_column_child",
                        )
                        .pull
                    )
                    parts = [tuple(p(d) for p in pulls) for d in result.data]
                    domain = SimpleSetDomain(partitions=jx.sort(set(parts)))
                else:
                    if not columns:
                        columns = transpose(*result.data)
                    parts = set(columns[i])
                    if e.is_groupby and None in parts:
                        allowNulls = True
                    parts -= {None}

                    if normalized_query.sort[i].sort == -1:
                        domain = SimpleSetDomain(partitions=wrap(sorted(parts, reverse=True)))
                    else:
                        domain = SimpleSetDomain(partitions=jx.sort(parts))

                dims.append(len(domain.partitions) + (1 if allowNulls else 0))
                edges.append(Data(name=e.name, allowNulls=allowNulls, domain=domain))

            data_cubes = {s["name"]: Matrix(dims=dims) for s in normalized_query.select.terms}

            r2c = index_to_coordinate(dims)  # WORKS BECAUSE THE DATABASE SORTED THE EDGES TO CONFORM
            for record, row in enumerate(result.data):
                coord = r2c(record)

                for i, s in enumerate(index_to_columns.values()):
                    if s.is_edge:
                        continue
                    if s.push_column_child == ".":
                        data_cubes[s.push_list_name][coord] = s.pull(row)
                    else:
                        data_cubes[s.push_list_name][coord][s.push_column_child] = s.pull(row)

            select = normalized_query.select.__data__()["select"]

            return Data(
                meta={"format": "cube"}, edges=edges, select=select, data={k: v.cube for k, v in data_cubes.items()},
            )
        elif format == "table" or (not format and normalized_query.groupby):
            column_names = [None] * (max(c.push_column_index for c in index_to_columns.values()) + 1)
            for c in index_to_columns.values():
                column_names[c.push_column_index] = c.push_column_name
            data = []
            for d in result.data:
                row = [None for _ in column_names]
                for s in index_to_columns.values():
                    if s.push_column_child == ".":
                        row[s.push_column_index] = s.pull(d)
                    elif s.num_push_columns:
                        tuple_value = row[s.push_column_index]
                        if tuple_value == None:
                            tuple_value = row[s.push_column_index] = [None] * s.num_push_columns
                        tuple_value[s.push_column_child] = s.pull(d)
                    elif row[s.push_column_index] == None:
                        row[s.push_column_index] = Data()
                        row[s.push_column_index][s.push_column_child] = s.pull(d)
                    else:
                        row[s.push_column_index][s.push_column_child] = s.pull(d)
                data.append(tuple(from_data(r) for r in row))

            output = Data(meta={"format": "table"}, header=column_names, data=data)
        elif format == "list":
            data = []
            for record in result.data:
                row = Data()
                for c in index_to_columns.values():
                    if c.push_column_child == ".":
                        row[c.push_list_name] = c.pull(record)
                    elif c.num_push_columns:
                        tuple_value = row[c.push_list_name]
                        if not tuple_value:
                            tuple_value = row[c.push_list_name] = [None] * c.num_push_columns
                        tuple_value[c.push_column_child] = c.pull(record)
                    else:
                        row[c.push_list_name][c.push_column_child] = c.pull(record)

                data.append(row)

            output = Data(meta={"format": "list"}, data=data)
        else:
            Log.error("unknown format {{format}}", format=format)


formats = {
    "value": "value",
    "list": "list",
    "cube": "cube",
}
