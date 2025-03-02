# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from mo_math import MIN

from jx_base.expressions.base_multi_op import BaseMultiOp
from jx_base.expressions.literal import Literal
from jx_base.expressions.literal import is_literal
from jx_base.expressions.null_op import NULL


class LeastOp(BaseMultiOp):
    """
    DECISIVE MINIMUM (SEE LeastOp FOR CONSERVATIVE MINIMUM)
    """

    def __call__(self, row, rownum=None, rows=None):
        mini = None
        for t in self.terms:
            v = t(row, rownum, rows)
            if v is None:
                if self.decisive:
                    continue
                else:
                    return None
            if mini is None:
                mini = v
            elif v < mini:
                mini = v
        return mini

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
                return lang.Literal(minimum)
        else:
            if minimum == None:
                output = lang.LeastOp(*terms, nulls=self.decisive)
            else:
                output = lang.LeastOp(lang.Literal(minimum), *terms, nulls=self.decisive)

        return output
