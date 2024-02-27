# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.literal import ZERO, ONE, is_literal
from jx_base.language import is_op, value_compare
from mo_json.types import JX_BOOLEAN


class SqlEqOp(Expression):
    _jx_type = JX_BOOLEAN

    def __init__(self, *terms):
        Expression.__init__(self, *terms)
        self.lhs, self.rhs = terms

    def __data__(self):
        return {"sql.eq": [self.lhs.__data__(), self.rhs.__data__()]}

    def missing(self, lang):
        return FALSE

    def __eq__(self, other):
        return is_op(other, SqlEqOp) and self.lhs == other.lhs and self.rhs == other.rhs

    def partial_eval(self, lang):
        lhs = self.lhs.partial_eval(lang)
        rhs = self.rhs.partial_eval(lang)

        if is_literal(lhs) and is_literal(rhs):
            return ZERO if value_compare(lhs.value, rhs.value) else ONE
        else:
            return lang.SqlEqOp(lhs, rhs)
