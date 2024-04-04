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
from mo_json.types import JX_TEXT


class StrictSubstringOp(Expression):
    """
    PLACEHOLDER FOR BASIC value.substring(start, end) (CAN NOT DEAL WITH NULLS)
    """

    _jx_type = JX_TEXT

    def __init__(self, value, start, end):
        Expression.__init__(self, value, start, end)
        self.value, self.start, self.end = value, start, end

    def __call__(self, row, rownum=None, rows=None):
        return self.value(row, rownum, rows)[self.start(row, rownum, rows) : self.end(row, rownum, rows)]

    def __data__(self):
        return {"strict.substring": [self.value.__data__(), self.start.__data__(), self.end.__data__()]}

    def map(self, map_):
        return StrictSubstringOp(self.value.map(map_), self.start.map(map_), self.end.map(map_),)

    def vars(self):
        return self.value.vars() | self.start.vars() | self.end.vars()

    def missing(self, lang):
        return FALSE

    def invert(self, lang):
        return FALSE
