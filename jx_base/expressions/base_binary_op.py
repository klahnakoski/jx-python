# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import is_missing

from jx_base.language import is_op

from jx_base.expressions._utils import builtin_ops
from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import is_literal, Literal
from jx_base.expressions.null_op import NULL
from mo_imports import expect
from mo_json.types import JX_NUMBER

OrOp, Variable, is_variable = expect("OrOp", "Variable", "is_variable")


class BaseBinaryOp(Expression):
    has_simple_form = True
    _jx_type = JX_NUMBER

    def __init__(self, lhs, rhs):
        Expression.__init__(self, lhs, rhs)
        self.lhs, self.rhs = lhs, rhs

    def __call__(self, row, rownum=None, rows=None):
        lhs = self.lhs(row, rownum, rows)
        rhs = self.rhs(row, rownum, rows)
        if is_missing(lhs) or is_missing(rhs):
            return None
        return builtin_ops[self.op](lhs, rhs)

    def __data__(self):
        if is_variable(self.lhs) and is_literal(self.rhs):
            return {self.op: {self.lhs.var: self.rhs.value}}
        else:
            return {self.op: [self.lhs.__data__(), self.rhs.__data__()]}

    def __eq__(self, other):
        if not is_op(other, self.__class__):
            return False
        return self.lhs == other.lhs and self.rhs == other.rhs

    def vars(self):
        return self.lhs.vars() | self.rhs.vars()

    def map(self, map_):
        return self.__class__([self.lhs.map(map_), self.rhs.map(map_)])

    def missing(self, lang):
        return OrOp(self.lhs.missing(lang), self.rhs.missing(lang))

    def partial_eval(self, lang):
        lhs = self.lhs.partial_eval(lang)
        rhs = self.rhs.partial_eval(lang)
        if is_literal(lhs) and is_literal(rhs):
            if lhs is NULL or rhs is NULL:
                return NULL
            return Literal(builtin_ops[self.op](lhs.value, rhs.value))
        return getattr(lang, self.__class__.__name__)(lhs, rhs)
