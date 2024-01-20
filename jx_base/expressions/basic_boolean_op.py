# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from mo_imports import export
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.null_op import NULL
from jx_base.expressions.not_op import NotOp
from mo_json.types import JX_BOOLEAN


class BasicBooleanOp(Expression):
    """
    FORCE VALUE TO BOOLEAN, USING COMMON SENSE
    * NULL IS FALSE
    * EMPTY STRING IS FALSE
    * ZERO IS FALSE
    """

    _jx_type = JX_BOOLEAN

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __data__(self):
        return {"basic.boolean": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return BasicBooleanOp(self.term.map(map_))

    def missing(self, lang):
        return FALSE

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)
        if term is NULL:
            return FALSE
        elif term.jx_type is JX_BOOLEAN:
            return term
        elif term is self.term:
            return self

        truthy = AndOp(
            NotOp(term.missing(lang)),
            NotOp(InOp(term, [Literal(""), Literal("F"), Literal("false"), NeOp(term, ZERO)])),
        ).partial_eval(lang)
        return truthy
