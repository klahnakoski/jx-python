# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions._utils import builtin_ops
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.literal import Literal
from jx_base.expressions.null_op import NULL
from jx_base.language import is_op
from mo_json.types import JX_NUMBER


class StrictMultiOp(Expression):
    """
    PLACEHOLDER FOR STRICT MULTI-VALUED OPERATIONS (CAN NOT DEAL WITH NULLS)
    """

    _jx_type = JX_NUMBER
    op = None

    def __init__(self, *terms):
        Expression.__init__(self, *terms)
        self.terms = terms

    def vars(self):
        output = set()
        for t in self.terms:
            output.update(t.vars())
        return output

    def map(self, map):
        return self.__class__([t.map(map) for t in self.terms])

    def __data__(self):
        return {self.op: [t.__data__() for t in self.terms]}

    def missing(self, lang):
        return FALSE

    def partial_eval(self, lang):
        acc = None
        terms = []
        for t in self.terms:
            simple = t.partial_eval(lang)
            if simple is NULL:
                pass
            elif is_op(simple, Literal):
                if acc is None:
                    acc = simple.value
                else:
                    acc = builtin_ops[self.op](acc, simple.value)
            else:
                terms.append(simple)
        if len(terms) == 0:
            if acc == None:
                return self.default.partial_eval(lang)
            else:
                return Literal(acc)
        else:
            if acc is not None:
                terms.append(Literal(acc))

            return self.__class__(*terms)
