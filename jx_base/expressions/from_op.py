# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import Expression, _jx_expression
from jx_base.expressions.sql_inner_join_op import SqlJoinOne
from jx_base.expressions.sql_left_joins_op import SqlLeftJoinsOp
from jx_base.language import is_op, is_expression
from jx_base.models.container import Container
from mo_dots import to_data


class FromOp(Expression):
    has_simple_form = True

    def __init__(self, frum):
        Expression.__init__(self, frum)
        self.frum = frum
        self._jx_type = frum.jx_type

    @classmethod
    def define(cls, expr):
        return FromOp(_jx_expression(to_data(expr)["from"], cls.lang))

        root, *rest = frum
        joins = []
        for join in rest:
            if not is_data(join):
                logger.error("can not handle yet: {join}", join=join)
            if "left_join" not in join:
                logger.error("Expecting a left join, not {join}", join=join)
            joins.append(SqlJoinOne(
                _jx_expression(join["left_join"], cls.lang), _jx_expression(coalesce(join.get("on"), True), cls.lang)
            ))

        return SqlLeftJoinsOp(_jx_expression(root, cls.lang), *joins)

    def __call__(self, row=None, rownum=None, rows=None):
        if is_expression(self.frum):
            return self.frum(row, rownum, rows)
        return self.frum

    @property
    def schema(self):
        return self.frum.schema

    def apply(self, container: Container):
        return container.query(self.frum)

    def __data__(self):
        return {"from": self.frum.__data__()}

    def vars(self):
        return self.frum.vars()

    def map(self, map):
        return FromOp(self.frum.map(map))

    def missing(self, lang):
        return self.frum.missing()

    def exists(self):
        return self.frum.exists()

    def invert(self, lang):
        return self.frum.invert()

    def partial_eval(self, lang):
        return FromOp(self.frum.partial_eval(lang))

    @property
    def jx_type(self):
        return self._jx_type

    def __eq__(self, other):
        if is_op(other, FromOp):
            return self.frum == other.frum
        return self.frum == other
