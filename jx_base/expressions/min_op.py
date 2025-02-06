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
from jx_base.expressions.least_op import LeastOp
from mo_json.types import JX_NUMBER


class MinOp(Expression):
    """
    DECISIVE MINIMUM (SEE LeastOp FOR CONSERVATIVE MINIMUM)
    """

    _jx_type = JX_NUMBER

    def __new__(cls, *terms, frum=None):
        if frum is not None:
            op = object.__new__(MinOp)
            op.__init__(frum=frum)
            return op
        elif len(terms) > 1:
            return LeastOp(*terms, nulls=True)
        else:
            op = object.__new__(MinOp)
            op.__init__(frum=terms[0])
            return op

    def __init__(self, *terms, frum=None):
        if terms:
            frum = terms[0]

        Expression.__init__(self, frum)
        self.frum = frum

    def __data__(self):
        return {"min": self.frum.__data__()}

    def vars(self):
        return self.frum.vars()

    def map(self, map_):
        return MinOp(frum=self.frum.map(map_))

    def missing(self, lang):
        return FALSE

    def partial_eval(self, lang):
        return MinOp(frum=self.frum.partial_eval(lang))
