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


class SqlLimitOp(Expression):
    def __init__(self, frum, limit):
        Expression.__init__(self, frum, limit)
        self.frum = frum
        self.limit = limit
