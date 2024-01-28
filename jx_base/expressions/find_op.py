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
from jx_base.expressions.literal import ZERO
from jx_base.expressions.literal import is_literal
from jx_base.expressions.null_op import NULL
from jx_base.expressions.variable import is_variable
from mo_dots import is_missing
from mo_json import JX_INTEGER


class FindOp(Expression):
    """
    RETURN INDEX OF find IN value, ELSE RETURN null
    """

    has_simple_form = True
    _jx_type = JX_INTEGER

    def __init__(self, value, find, start=ZERO):
        Expression.__init__(self, value, find)
        self.value, self.find, self.start = value, find, start
        if self.start is NULL:
            self.start = ZERO

    def __eq__(self, other):
        if not isinstance(other, FindOp):
            return False
        return self.value == other.value and self.find == other.find and self.start == other.start

    def __data__(self):
        if is_variable(self.value) and is_literal(self.find):
            output = {
                "find": {self.value.var: self.find.value},
                "start": self.start.__data__(),
            }
        else:
            output = {
                "find": [self.value.__data__(), self.find.__data__()],
                "start": self.start.__data__(),
            }
        return output

    def __call__(self, row, rownum=None, rows=None):
        value = self.value(row, rownum, rows)
        if is_missing(value):
            return None
        find = self.find(row, rownum, rows)
        if is_missing(find):
            return None
        start = self.start(row, rownum, rows)

        i = value.find(find, start)
        if i == -1:
            return None
        return i

    def vars(self):
        return self.value.vars() | self.find.vars() | self.start.vars()

    def map(self, map_):
        return FindOp(self.value.map(map_), self.find.map(map_), self.start.map(map_))

    def invert(self, lang):
        return lang.MissingOp(self)
