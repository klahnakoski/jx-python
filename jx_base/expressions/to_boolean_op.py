# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions.expression import Expression, TRUE
from mo_imports import export
from mo_json import JX_BOOLEAN


class ToBooleanOp(Expression):
    """
    CONVERT VALUE TO BOOLEAN, OR KEEP AS BOOLEAN
    """

    _jx_type = JX_BOOLEAN

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __data__(self):
        return {"boolean": self.term.__data__()}

    def __eq__(self, other):
        return isinstance(other, ToBooleanOp) and self.term == other.term

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return ToBooleanOp(self.term.map(map_))

    def missing(self, lang):
        return self.term.missing(lang)

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)
        if term.jx_type == JX_BOOLEAN or term.missing(lang) is TRUE:
            return term
        elif term is self.term:
            return self
        return ToBooleanOp(term)


export("jx_base.expressions.and_op", ToBooleanOp)
