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
from mo_dots import Null, exists


class AvgOp(Expression):
    def __init__(self, frum):
        Expression.__init__(self, frum)
        self.frum = frum

    def __call__(self, row=None, rownum=None, rows=None):
        values = [v for v in enlist(self.frum(row, rownum, rows)) if exists(v)]
        if not values:
            return Null
        return sum(values) / len(values)
