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
from jx_base.expressions.literal import NULL
from jx_base.expressions.to_boolean_op import ToBooleanOp
from jx_base.expressions.true_op import TRUE
from jx_base.language import is_op
from mo_dots import is_sequence
from mo_imports import expect
from mo_json.types import JX_BOOLEAN, union_type
from mo_logs import Log

WhenOp = expect("WhenOp")


class CaseOp(Expression):
    def __init__(self, *terms):
        if not is_sequence(terms):
            Log.error("case expression requires a list of `when` sub-clauses")
        Expression.__init__(self, *terms)
        if len(terms) == 0:
            Log.error("Expecting at least one clause")

        if is_op(terms[-1], WhenOp):
            self._whens, self._else = terms, NULL
        else:
            self._whens, self._else = terms[:-1], terms[-1]

        for w in self._whens:
            if not is_op(w, WhenOp) or w.els_ is not NULL:
                Log.error("case expression does not allow `else` clause in `when` sub-clause")

    @property
    def whens(self):
        return self._whens

    @property
    def els_(self):
        return self._else

    def __data__(self):
        return {"case": [*(w.__data__() for w in self._whens), self._else.__data__()]}

    def __eq__(self, other):
        if is_op(other, CaseOp):
            return all(s == o for s, o in zip(self.whens, other.whens)) and self._else == other._else

    def vars(self):
        output = set()
        for w in self.whens:
            output |= w.vars()
        output |= self._else.vars()
        return output

    def map(self, map_):
        return CaseOp(*(w.map(map_) for w in self.whens), self._else.map(map_))

    def missing(self, lang):
        whens = [*(WhenOp(w.when, then=w.then.missing(lang)) for w in self.whens), self._else.missing(lang)]

        return CaseOp(*whens).partial_eval(lang)

    def invert(self, lang):
        return CaseOp(
            *(WhenOp(w.when, then=w.then.invert(lang)) for w in self.whens), self._else
        ).partial_eval(lang)

    def partial_eval(self, lang):
        if self.jx_type is JX_BOOLEAN:
            nots = []
            ors = []
            for w in self.whens:
                ors.append(lang.AndOp(*nots, w.when, w.then))
                nots.append(lang.NotOp(w.when))
            ors.append(lang.AndOp(*nots, self.els_))
            return lang.OrOp(*ors).partial_eval(lang)

        whens = []
        for w in self.whens:
            when = ToBooleanOp(w.when).partial_eval(lang)
            if when is TRUE:
                whens.append(w.then.partial_eval(lang))
                break
            elif when is FALSE or when is NULL:
                pass
            else:
                then = w.then.partial_eval(lang)
                if is_op(then, CaseOp):
                    for ww in then.whens:
                        whens.append(lang.WhenOp(AndOp(when, ww.when).partial_eval(lang), then=ww.then))
                        if then.els_ is not NULL:
                            whens.append(lang.WhenOp(when, then.els_))
                elif is_op(then, WhenOp):
                    whens.append(lang.WhenOp(AndOp(when, then.when).partial_eval(lang), then=then.then))
                    whens.append(lang.WhenOp(when, then.els_))
                else:
                    whens.append(lang.WhenOp(when, then=then))

        _else = self._else.partial_eval(lang)

        if len(whens) == 0:
            return _else
        elif len(whens) == 1:
            return lang.WhenOp(whens[0].when, then=whens[0].then, **{"else": _else})
        else:
            return lang.CaseOp(*whens, _else)

    @property
    def jx_type(self):
        return union_type(*(w.then.jx_type if is_op(w, WhenOp) else w.jx_type for w in self.whens))
