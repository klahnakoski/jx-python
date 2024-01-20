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
from mo_json.types import JX_NUMBER
from jx_base.expressions.most_op import MostOp


class MaxOp(Expression):
    """
    DECISIVE MAXIMUM (SEE MostOp FOR CONSERVATIVE MAXIMUM)
    """

    _jx_type = JX_NUMBER

    def __new__(cls, *terms, frum=None):
        if frum is not None:
            op = object.__new__(MaxOp)
            op.__init__(frum=frum)
            return op
        elif len(terms) > 1:
            return MostOp(*terms, nulls=True)
        else:
            op = object.__new__(MaxOp)
            op.__init__(frum=terms[0])
            return op

    def __init__(self, *terms, frum=None):
        if terms:
            frum = terms[0]

        Expression.__init__(self, frum)
        self.frum = frum

    def __data__(self):
        return {"max": self.frum.__data__()}

    def vars(self):
        return self.frum.vars()

    def map(self, map_):
        return MaxOp(frum=self.frum.map(map_))

    def missing(self, lang):
        return Missing(self.frum.missing(lang))

    def partial_eval(self, lang):
        return MaxOp(frum=self.frum.partial_eval(lang))
