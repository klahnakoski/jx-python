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


class CardinalityOp(Expression):

    def __init__(self, frum):
        Expression.__init__(self, frum)
        self.frum = frum

    def __call__(self, row, rownum, rows):
        values = self.terms(row, rownum, rows)
        return len(set(values))

    def __data__(self):
        return {"cardinality": self.frum.__data__()}