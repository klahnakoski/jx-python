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
from jx_base.expressions.false_op import FALSE
from jx_base.language import is_op
from mo_json.types import JX_BOOLEAN


class AllOp(Expression):
    """
    DECISIVE AND
    """

    _jx_type = JX_BOOLEAN

    def __init__(self, frum):
        Expression.__init__(self, frum)
        self.frum = frum

    def __data__(self):
        return {"all": self.frum}

    def __call__(self, row, rownum=None, rows=None):
        for a in enlist(self.fruma(row, rownum, rows)):
            if is_missing(a) or a is False:
                return False
        return True

    def __eq__(self, other):
        if is_op(other, AllOp):
            return self.frum == other.frum
        return False

    def vars(self):
        return self.frum.vars()

    def map(self, map_):
        return AllOp(self.frum.map(map_))

    def missing(self, lang):
        return FALSE

    def partial_eval(self, lang):
        return AllOp(self.frum.partial_eval(lang))
