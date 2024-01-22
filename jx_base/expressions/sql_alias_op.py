# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import Expression, Literal
from jx_base.language import is_op


class SqlAliasOp(Expression):

    def __init__(self, name, value):
        Expression.__init__(self, Literal(name), value)
        self.name = name
        self.value = value

    def __data__(self):
        return {self.name: self.value.__data__()}

    def missing(self, lang):
        return self.value.missing(lang)

    def __eq__(self, other):
        if not is_op(other, SqlAliasOp):
            return False
        return self.name == other.name and self.value == other.value

    def __repr__(self):
        return f"SqlAliasOp({self.name}={self.value})"
