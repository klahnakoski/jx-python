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


class AnyOp(Expression):
    """
    DECISIVE OR
    """

    _jx_type = JX_BOOLEAN
    default = FALSE  # ADD THIS TO terms FOR NO EFFECT

    def __init__(self, frum=None):
        Expression.__init__(self, frum)
        self.frum = frum

    def __data__(self):
        return {"any": self.frum.__data__()}

    def vars(self):
        return self.frum.vars()

    def map(self, map_):
        return AnyOp(self.terms.map(map_))

    def missing(self, lang):
        return FALSE

    def __call__(self, row=None, rownum=None, rows=None):
        for v in self.frum(row, rownum, rows):
            if is_missing(v):
                continue
            if v is True:
                return True
        return False

    def __eq__(self, other):
        if not is_op(other, AnyOp):
            return False
        return len(self.frum) == len(other.frum)

    def partial_eval(self, lang):
        return AnyOp(self.frum.partial_eval(lang))
