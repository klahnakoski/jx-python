# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import NULL, FALSE
from jx_base.expressions.expression import Expression
from mo_json import JX_INTEGER


class SqlSubstrOp(Expression):
    _jx_type = JX_INTEGER

    def __init__(self, value, start, length=NULL):
        Expression.__init__(self, value, start, length)
        self.value, self.start, self.length = value, start, length

    def __data__(self):
        return {"sql.substr": [self.value.__data__(), self.start.__data__(), self.length.__data__()]}

    def vars(self):
        return self.value.vars() | self.start.vars() | self.length.vars()

    def missing(self, lang):
        return FALSE
