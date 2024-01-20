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
from jx_base.expressions.variable import Variable, is_variable
from jx_base.language import is_op
from mo_imports import export
from mo_dots import concat_field
from mo_json import JX_ANY, ARRAY, ARRAY_KEY


class GetOp(Expression):
    """
    REPRESENT ATTRIBUTE ACCESS, FLATTENING THE RESULT
    """

    has_simple_form = True

    def __init__(self, frum, *offsets):
        Expression.__init__(self, frum, *offsets)
        self.frum = frum
        self.offsets = offsets

    def partial_eval(self, lang):
        var = self.frum.partial_eval(lang)
        offsets = tuple(o.partial_eval(lang) for o in self.offsets)
        if var.op == GetOp.op:
            return lang.GetOp(var.frum, *var.offsets + offsets)
        return lang.GetOp(var, *offsets)

    def __data__(self):
        if is_variable(self):
            return self.var
        return {"get": [self.frum.__data__(), *(o.__data__() for o in self.offsets)]}

    def __call__(self, row, rownum=None, rows=None):
        output = self.frum(row, rownum, rows)
        for o in self.offsets:
            ov = o(row, rownum, rows)
            try:
                output = getattr(output, ov)
            except:
                try:
                    output = output[ov]
                except:
                    break
        return output

    @property
    def var(self):
        var_name = self.frum.var  # expecting Variable
        if var_name == "row":
            var_name = "."
        for lit in self.offsets:  # expecting Literal
            var_name = concat_field(var_name, lit.value)
        return var_name

    @property
    def jx_type(self):
        output = self.frum.jx_type
        for o in self.offsets:
            while output == ARRAY:
                output = output[ARRAY_KEY]
            if is_literal(o):
                output = output[o.value]
                if output is None:
                    output = JX_ANY
            else:
                output = JX_ANY
        return output

    def vars(self):
        if is_variable(self):
            return {self.var}
        output = self.frum.vars()
        for o in self.offsets:
            output |= o.vars()
        return output

    def map(self, map_):
        try:
            return Variable(map_[self.var])
        except Exception as cause:
            return GetOp(self.frum.map(map_), *(o.map(map_) for o in self.offsets))

    def __eq__(self, other):
        return (
            is_op(other, GetOp)
            and other.frum == self.frum
            and all(o == s for s, o in zip(self.offsets, other.offsets))
        )


export("jx_base.expressions.variable", GetOp)
