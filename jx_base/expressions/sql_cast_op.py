# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import Expression
from jx_base.language import is_op
from mo_json import to_jx_type


class SqlCastOp(Expression):
    """
    MUCH LIKE NameOp, BUT FOR SQL
    """

    def __init__(self, value, es_type):
        Expression.__init__(self, value)
        self.value = value
        self.es_type = es_type
        self._jx_type = to_jx_type(es_type)

    def __data__(self):
        return {"sql.cast": self.value.__data__()}

    def missing(self, lang):
        return self.value.missing(lang)

    def __eq__(self, other):
        return is_op(other, SqlCastOp) and self.value == other.value and self.es_type == other.es_type

    def __repr__(self):
        return f"SqlCastOp({self.value}, {self.es_type})"
