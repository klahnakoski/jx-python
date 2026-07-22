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
from jx_base.utils import enlist
from mo_dots import exists


class CardinalityOp(Expression):
    def __init__(self, frum):
        Expression.__init__(self, frum)
        self.frum = frum

    def __call__(self, row, rownum=None, rows=None):
        values = enlist(self.frum(row, rownum, rows))
        return len(set(v for v in values if exists(v)))

    def __data__(self):
        return {"cardinality": self.frum.__data__()}

    def vars(self):
        return self.frum.vars()

    def map(self, map_):
        return CardinalityOp(self.frum.map(map_))

    def partial_eval(self, lang):
        return lang.CardinalityOp(self.frum.partial_eval(lang))
