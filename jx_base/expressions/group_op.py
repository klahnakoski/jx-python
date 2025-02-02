# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions.expression import Expression, MissingOp
from mo_json import array_of


class GroupOp(Expression):
    """
    return a series of {"group": group, "part": list_of_rows_for_group}
    """

    def __init__(self, frum, group):
        Expression.__init__(self, frum, group)
        self.frum, self.group = frum, group

    def __data__(self):
        return {"group": [self.frum.__data__(), self.group.__data__()]}

    def vars(self):
        return self.frum.vars() | self.group.vars()

    def map(self, map_):
        return GroupOp(self.frum.map(map_), self.group.map(map_))

    @property
    def jx_type(self):
        return array_of(self.frum.jx_type)

    def missing(self, lang):
        return MissingOp(self)

    def invert(self, lang):
        return self.missing(lang)
