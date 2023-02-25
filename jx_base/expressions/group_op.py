# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_logs import Log

from jx_base.expressions.expression import Expression, MissingOp
from mo_json import JX_ARRAY, JxType, array_of


class GroupOp(Expression):
    """
    return a series of {"group": group, "part": list_of_rows_for_group}
    """
    def __init__(self, frum, select):
        Expression.__init__(self, frum, select)
        self.frum, self.select = frum, select
        if self.frum.type != JX_ARRAY:
            Log.error("expecting an array")

    def __data__(self):
        return {"group": [self.frum.__data(), self.select.__data__()]}

    def vars(self):
        return self.frum.vars() | self.select.vars()

    def map(self, map_):
        return GroupOp(self.frum.map(map_), self.select.map(map_))

    @property
    def type(self):
        return array_of(self.frum.type) | JxType(group=self.select.type)

    def missing(self, lang):
        return MissingOp(self)

    def invert(self, lang):
        return self.missing(lang)
