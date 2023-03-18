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
from jx_base.expressions.literal import is_literal
from mo_json import JX_ANY


class GetOp(Expression):
    """
    REPRESENT ATTRIBUTE ACCESS, FLATTENING THE RESULT
    """

    has_simple_form = True

    def __init__(self, var, *offsets):
        Expression.__init__(self, var, *offsets)
        self.var = var
        self.offsets = offsets

    def partial_eval(self, lang):
        var = self.var.partial_eval(lang)
        offsets = tuple(o.partial_eval(lang) for o in self.offsets)
        if var.op == GetOp.op:
            return GetOp(var.var, *var.offsets + offsets)
        return GetOp(var, *offsets)

    def __data__(self):
        if is_literal(self.var) and len(self.offsets) == 1 and is_literal(self.offset):
            return {"get": {self.var.json, self.offsets[0].value}}
        else:
            return {"get": [self.var.__data__(), *(o.__data__() for o in self.offsets)]}

    @property
    def type(self):
        output = self.var.type
        for o in self.offsets:
            if is_literal(o):
                output = output[o.value]
            else:
                output = JX_ANY
        return output

    def vars(self):
        output = self.var.vars()
        for o in self.offsets:
            output |= o.vars()
        return output

    def map(self, map_):
        return GetOp(self.var.map(map_), *(o.map(map_) for o in self.offsets))

    def __eq__(self, other):
        return (
            isinstance(other, GetOp)
            and other.var == self.var
            and all(o == s for s, o in zip(self.offsets, other.offsets))
        )
