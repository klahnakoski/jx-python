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
from jx_base.expressions.is_text_op import IsTextOp
from jx_base.language import is_op
from mo_json.types import JX_BOOLEAN


class StrictStartsWithOp(Expression):
    """
    PLACEHOLDER FOR BASIC value.startsWith(find, start) (CAN NOT DEAL WITH NULLS)
    """

    _jx_type = JX_BOOLEAN

    def __init__(self, *params):
        Expression.__init__(self, *params)
        self.value, self.prefix = params

    def __call__(self, row, rownum=None, rows=None):
        if self.value(row, rownum, rows).startswith(self.prefix(row, rownum, rows)):
            return True
        else:
            return False

    def __data__(self):
        return {"strict.startsWith": [self.value.__data__(), self.prefix.__data__()]}

    def __eq__(self, other):
        if is_op(other, StrictStartsWithOp):
            return self.value == other.value and self.prefix == other.prefix

    def vars(self):
        return self.value.vars() | self.prefix.vars()

    def map(self, map_):
        return self.lang.StrictStartsWithOp(self.value.map(map_), self.prefix.map(map_),)

    def missing(self, lang):
        return FALSE

    def partial_eval(self, lang):
        return lang.StrictStartsWithOp(
            IsTextOp(self.value).partial_eval(lang), IsTextOp(self.prefix).partial_eval(lang),
        )
