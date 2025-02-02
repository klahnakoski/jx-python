# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions.base_inequality_op import BaseInequalityOp

from jx_base.expressions.strict_eq_op import StrictEqOp
from jx_base.expressions.nested_op import NestedOp
from jx_base.expressions.not_op import NotOp
from jx_base.expressions.or_op import OrOp
from jx_base.expressions.variable import IDENTITY
from jx_base.language import is_op


class NeOp(BaseInequalityOp):

    def __call__(self, row, rownum=None, rows=None):
        v1 = self.lhs(row, rownum, rows)
        v2 = self.rhs(row, rownum, rows)
        if v1 == None or v2 == None:
            return False
        return v1 != v2

    def invert(self, lang):
        return OrOp(self.lhs.missing(lang), self.rhs.missing(lang), StrictEqOp(self.lhs, self.rhs),).partial_eval(lang)

    def partial_eval(self, lang):
        lhs = self.lhs.partial_eval(lang)
        rhs = self.rhs.partial_eval(lang)

        if is_op(lhs, NestedOp):
            return NestedOp(
                path=lhs.nested_path.partial_eval(lang),
                select=IDENTITY,
                where=lang.AndOp(lhs.where, NeOp(lhs.select, rhs)).partial_eval(lang),
                sort=lhs.sort.partial_eval(lang),
                limit=lhs.limit.partial_eval(lang),
            ).partial_eval(lang)

        output = lang.AndOp(lhs.exists(), rhs.exists(), NotOp(StrictEqOp(lhs, rhs))).partial_eval(lang)
        return output
