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


class StatsOp(Expression):
    """
    THE STATS OBJECT (count, std, min, max, sum, sos, var, avg).
    MEDIAN IS NOT INCLUDED; USE PercentilesOp FOR THAT.
    """

    def __init__(self, frum):
        Expression.__init__(self, frum)
        self.frum = frum

    def __data__(self):
        return {"stats": self.frum.__data__()}
