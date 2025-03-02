# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.first_op import FirstOp
from jx_base.expressions.null_op import NULL
from jx_base.language import is_op
from mo_imports import export
from mo_json import union_type
from mo_dots import exists


class CoalesceOp(Expression):
    has_simple_form = True

    def __init__(self, *terms):
        Expression.__init__(self, *terms)
        self.terms = terms
        self._jx_type = union_type(*(t.jx_type for t in terms))

    def __call__(self, row, row_num, rows):
        for t in self.terms:
            v = t(row, row_num, rows)
            if exists(v):
                return v
        return None

    def __data__(self):
        return {"coalesce": [t.__data__() for t in self.terms]}

    def __eq__(self, other):
        if is_op(other, CoalesceOp):
            if len(self.terms) == len(other.terms):
                return all(s == o for s, o in zip(self.terms, other.terms))
        return False

    def missing(self, lang):
        # RETURN true FOR RECORDS THE WOULD RETURN NULL
        return lang.AndOp(*(v.missing(lang) for v in self.terms))

    def vars(self):
        output = set()
        for v in self.terms:
            output |= v.vars()
        return output

    def map(self, map_):
        return CoalesceOp(*(v.map(map_) for v in self.terms))

    def partial_eval(self, lang):
        terms = []
        for t in self.terms:
            simple = FirstOp(t).partial_eval(lang)
            if simple is NULL:
                pass
            elif simple.missing(lang) is FALSE:
                terms.append(simple)
                break
            else:
                terms.append(simple)

        if len(terms) == 0:
            return NULL
        elif len(terms) == 1:
            return terms[0]
        else:
            return lang.CoalesceOp(*terms)


export("jx_base.expressions.base_multi_op", CoalesceOp)
