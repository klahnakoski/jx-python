# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions.base_inequality_op import BaseInequalityOp
from jx_base.expressions.literal import is_literal
from jx_base.expressions.not_op import NotOp
from mo_json import JX_BOOLEAN


class BasicEqOp(BaseInequalityOp):
    """
    STRICT `==` OPERATOR (CAN NOT DEAL WITH NULLS)
    """
    op = "basic.eq"

    def __call__(self, row, rownum=None, rows=None):
        return self.lhs(row, rownum, rows) == self.rhs(row, rownum, rows)

    def partial_eval(self, lang):
        lhs = self.lhs.partial_eval(lang)
        rhs = self.rhs.partial_eval(lang)
        if is_literal(rhs) and rhs.value == 0:
            lhs._jx_type = JX_BOOLEAN
            return NotOp(lhs)
        if is_literal(lhs) and lhs.value == 0:
            rhs._jx_type = JX_BOOLEAN
            return NotOp(rhs)
        return lang.BasicEqOp(lhs, rhs)