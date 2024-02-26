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
from mo_json import JX_INTEGER


class SqlInstrOp(Expression):
    """
    CONSERVATIVE indexOf OPERATION (null PARAMETERS RETURN null)
    RETURN POSITION OF find IN value
    RETURN INDEX OF find IN value (FIRST CHARACTER IS 1)
    RETURN 0 IF NOT FOUND
    """

    _jx_type = JX_INTEGER

    def __init__(self, value, find):
        Expression.__init__(self, value, find)
        self.value, self.find = value, find

    def __eq__(self, other):
        if not isinstance(other, SqlInstrOp):
            return False
        return self.value == other.value and self.find == other.find

    def __data__(self):
        return {"sql.instr": [self.value.__data__(), self.find.__data__()]}

    def vars(self):
        return self.value.vars() | self.find.vars()

    def missing(self, lang):
        return FALSE
