# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions._utils import _jx_expression
from jx_base.expressions.and_op import AndOp
from jx_base.expressions.base_inequality_op import BaseInequalityOp
from jx_base.expressions.strict_eq_op import StrictEqOp
from jx_base.expressions.case_op import CaseOp
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.literal import is_literal, Literal
from jx_base.expressions.true_op import TRUE
from jx_base.expressions.variable import Variable
from jx_base.language import value_compare
from mo_dots import is_many, is_data
from mo_imports import expect
from mo_imports import export
from mo_logs import Log

InOp, WhenOp = expect("InOp", "WhenOp")


class EqOp(BaseInequalityOp):
    def __new__(cls, *terms):
        if is_many(terms):
            return object.__new__(cls)

        items = terms.items()
        if len(items) == 1:
            if is_many(items[0][1]):
                return InOp(items[0])
            else:
                return EqOp(items[0])
        else:
            acc = []
            for lhs, rhs in items:
                if rhs.json.startswith("["):
                    acc.append(InOp(Variable(lhs), rhs))
                else:
                    acc.append(EqOp(Variable(lhs), rhs))
            return AndOp(acc)

    @classmethod
    def define(cls, expr):
        items = list(expr.items())
        if len(items) != 1:
            Log.error("expecting single property")
        op, terms = items[0]
        if op not in ("eq", "term"):
            Log.error("Expecting eq op")
        if is_many(terms):
            return EqOp(*(_jx_expression(e, cls.lang) for e in terms))
        elif is_data(terms):
            items = list(terms.items())
            if len(items) == 1:
                lhs, rhs = items[0]
                return EqOp(Variable(lhs), Literal(rhs))
            else:
                return AndOp(*(EqOp(Variable(lhs), Literal(rhs)) for lhs, rhs in items))
        else:
            Log.error("do not not know what to do")

    def __call__(self, row, rownum=None, rows=None):
        return self.lhs(row, rownum, rows) == self.rhs(row, rownum, rows)

    def partial_eval(self, lang):
        lhs = self.lhs.partial_eval(lang)
        rhs = self.rhs.partial_eval(lang)

        if is_literal(lhs) and is_literal(rhs):
            return FALSE if value_compare(lhs.value, rhs.value) else TRUE
        else:
            return lang.EqOp(lhs, rhs)


export("jx_base.expressions.strict_in_op", EqOp)
