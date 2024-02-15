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
from jx_base.expressions.false_op import FALSE
from jx_base.language import is_op
from mo_json.types import JX_BOOLEAN


class SqlIsNullOp(Expression):
    _data_type = JX_BOOLEAN

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __data__(self):
        return {"sql.is_null": self.term.__data__()}

    def missing(self, lang):
        return FALSE

    def __eq__(self, other):
        return is_op(other, SqlIsNullOp) and self.term == other.term
