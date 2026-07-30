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
from mo_json import JX_NUMBER


class AvgOp(Expression):
    """
    DECISIVE AVERAGE (THE MEAN OF THE COLLECTION, NULLS SKIPPED)
    """

    _jx_type = JX_NUMBER

    def __init__(self, *terms, frum=None):
        if terms:
            frum = terms[0]
        Expression.__init__(self, frum)
        self.frum = frum

    def __data__(self):
        return {"avg": self.frum.__data__()}

    def vars(self):
        return self.frum.vars()

    def join_vars(self):
        return set()  # AN AGGREGATE OVER A COLLECTION BRINGS ITS OWN SOURCE

    def map(self, map_):
        return AvgOp(frum=self.frum.map(map_))

    def partial_eval(self, lang):
        return AvgOp(frum=self.frum.partial_eval(lang))
