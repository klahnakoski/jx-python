# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.strict_substring_op import StrictSubstringOp
from jx_base.expressions.coalesce_op import CoalesceOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.length_op import LengthOp
from jx_base.expressions.literal import ZERO
from jx_base.expressions.literal import is_literal
from jx_base.expressions.max_op import MaxOp
from jx_base.expressions.min_op import MinOp
from jx_base.expressions.or_op import OrOp
from jx_base.expressions.variable import is_variable
from jx_base.expressions.when_op import WhenOp
from mo_json.types import JX_TEXT


class NotLeftOp(Expression):
    has_simple_form = True
    _jx_type = JX_TEXT

    def __init__(self, value, length):
        Expression.__init__(self, value, length)
        self.value, self.length = value, length

    def __data__(self):
        if is_variable(self.value) and is_literal(self.length):
            return {"not_left": {self.value.var: self.length.value}}
        else:
            return {"not_left": [self.value.__data__(), self.length.__data__()]}

    def vars(self):
        return self.value.vars() | self.length.vars()

    def map(self, map_):
        return NotLeftOp(self.value.map(map_), self.length.map(map_))

    def missing(self, lang):
        return OrOp(self.value.missing(lang), self.length.missing(lang))

    def partial_eval(self, lang):
        value = self.value.partial_eval(lang)
        length = self.length.partial_eval(lang)

        if length is ZERO:
            return value

        max_length = CoalesceOp(LengthOp(value), ZERO)
        output = WhenOp(
            self.missing(lang),
            **{"else": StrictSubstringOp(value, MaxOp(ZERO, MinOp(length, max_length)), max_length)}
        ).partial_eval(lang)
        return output
