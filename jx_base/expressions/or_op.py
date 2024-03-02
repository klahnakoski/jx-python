# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.and_op import AndOp
from jx_base.expressions.base_multi_op import BaseMultiOp
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.null_op import NULL
from jx_base.expressions.true_op import TRUE
from jx_base.language import is_op
from mo_imports import export
from mo_json.types import JX_BOOLEAN


class OrOp(BaseMultiOp):
    _jx_type = JX_BOOLEAN

    def missing(self, lang):
        if self.decisive:
            return FALSE
        return OrOp(*(t.missing(lang) for t in self.terms))

    def invert(self, lang):
        return lang.AndOp(*(t.invert(lang) for t in self.terms)).partial_eval(lang)

    def __call__(self, row=None, rownum=None, rows=None):
        return any(t(row, rownum, rows) for t in self.terms)

    def __contains__(self, item):
        return any(item in t for t in self.terms)

    def partial_eval(self, lang):
        terms = []
        ands = []
        for t in self.terms:
            simple = lang.ToBooleanOp(t).partial_eval(lang)
            if simple is TRUE:
                return TRUE
            elif simple is FALSE or simple is NULL:
                continue
            elif is_op(simple, OrOp):
                terms.extend([tt for tt in simple.terms if tt not in terms])
            elif is_op(simple, AndOp):
                ands.append(simple)
            elif simple not in terms:
                terms.append(simple)

        if ands:  # REMOVE TERMS THAT ARE MORE RESTRICTIVE THAN OTHERS
            for a in ands:
                for tt in a.terms:
                    if tt in terms:
                        break
                else:
                    terms.append(a)

        if len(terms) == 0:
            return FALSE
        if len(terms) == 1:
            return terms[0]
        return lang.OrOp(*terms)


export("jx_base.expressions.and_op", OrOp)
export("jx_base.expressions.base_binary_op", OrOp)
export("jx_base.expressions.base_multi_op", OrOp)
