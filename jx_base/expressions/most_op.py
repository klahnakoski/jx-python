# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.base_multi_op import BaseMultiOp
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.literal import Literal, is_literal
from jx_base.expressions.null_op import NULL
from mo_json.types import JX_NUMBER
from mo_math import MAX


class MostOp(BaseMultiOp):
    """
    CONSERVATIVE MAXIMUM (SEE MaxOp FOR DECISIVE MAXIMUM)
    """

    _jx_type = JX_NUMBER

    def __init__(self, *terms, nulls=None):
        BaseMultiOp.__init__(self, *terms, nulls=nulls)

    def __data__(self):
        return {"max": [t.__data__() for t in self.terms]}

    def vars(self):
        output = set()
        for t in self.terms:
            output |= t.vars()
        return output

    def map(self, map_):
        return MostOp(*(t.map(map_) for t in self.terms))

    def missing(self, lang):
        return FALSE

    def partial_eval(self, lang):
        maximum = None
        terms = []
        for t in self.terms:
            simple = t.partial_eval(lang)
            if simple is NULL:
                pass
            elif is_literal(simple):
                maximum = MAX([maximum, simple.value])
            else:
                terms.append(simple)
        if len(terms) == 0:
            if maximum is None:
                return NULL
            else:
                return Literal(maximum)
        else:
            if maximum is None:
                output = MostOp(*terms, nulls=self.decisive)
            else:
                output = MostOp(Literal(maximum), *terms, nulls=self.decisive)

        return output
