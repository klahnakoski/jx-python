# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.eq_op import EqOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.literal import ZERO, ONE
from jx_base.expressions.literal import is_literal
from jx_base.expressions.or_op import OrOp
from mo_json.types import JX_NUMBER


class FloorOp(Expression):
    has_simple_form = True
    _jx_type = JX_NUMBER

    def __init__(self, lhs, rhs=ONE):
        Expression.__init__(self, lhs, rhs)
        self.lhs, self.rhs = lhs, rhs

    def __data__(self):
        if is_variable(self.lhs) and is_literal(self.rhs):
            return {"floor": {self.lhs.var, self.rhs.value}}
        else:
            return {"floor": [self.lhs.__data__(), self.rhs.__data__()]}

    def vars(self):
        return self.lhs.vars() | self.rhs.vars()

    def map(self, map_):
        return FloorOp(self.lhs.map(map_), self.rhs.map(map_))

    def missing(self, lang):
        return OrOp(self.lhs.missing(lang), self.rhs.missing(lang), EqOp(self.rhs, ZERO),)
