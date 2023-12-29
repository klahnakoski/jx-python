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
from jx_base.expressions.literal import Literal
from jx_base.expressions.literal import is_literal
from jx_base.expressions.null_op import NULL
from jx_base.expressions.or_op import OrOp
from mo_json.types import JX_NUMBER
from mo_math import MIN


class LeastOp(BaseMultiOp):
    """
    DECISIVE MINIMUM (SEE LeastOp FOR CONSERVATIVE MINIMUM)
    """

    _jx_type = JX_NUMBER

    def __init__(self, *terms, nulls=None):
        BaseMultiOp.__init__(self, *terms, nulls=nulls)

    def __data__(self):
        return {
            "min": [t.__data__() for t in self.terms],
        }

    def vars(self):
        output = set()
        for t in self.terms:
            output |= t.vars()
        return output

    def map(self, map_):
        return LeastOp(*(t.map(map_) for t in self.terms))

    def missing(self, lang):
        return OrOp(*(t.missing(lang) for t in self.terms))

    def partial_eval(self, lang):
        minimum = None
        terms = []
        for t in self.terms:
            simple = t.partial_eval(lang)
            if simple is NULL:
                pass
            elif is_literal(simple):
                minimum = MIN([minimum, simple.value])
            else:
                terms.append(simple)
        if len(terms) == 0:
            if minimum == None:
                return NULL
            else:
                return Literal(minimum)
        else:
            if minimum == None:
                output = LeastOp(*terms, nulls=self.decisive)
            else:
                output = LeastOp(Literal(minimum), *terms, nulls=self.decisive)

        return output
