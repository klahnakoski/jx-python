# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions.expression import Expression, jx_expression, MissingOp
from jx_base.expressions.literal import TRUE
from jx_base.language import JX
from jx_base.utils import is_true
from mo_dots import is_many, to_data


class FilterOp(Expression):
    def __init__(self, frum, predicate):
        Expression.__init__(self, frum, predicate)
        self.frum, self.predicate = frum, predicate

    def __call__(self, row=None, rownum=None, rows=None):
        frum = self.frum(row, rownum, rows)
        if self.predicate is TRUE:
            return frum
        return [
            r
            for i, r in enumerate(to_data(d) for d in frum)
            if is_true(self.predicate(r, i, frum))
        ]

    def __data__(self):
        return {"filter": [self.frum.__data__(), self.predicate.__data__()]}

    def vars(self):
        return self.frum.vars() | self.predicate.vars()

    def map(self, map_):
        return FilterOp(self.frum.map(map_), self.predicate.map(map_))

    @property
    def jx_type(self):
        return self.frum.jx_type

    def missing(self, lang):
        return MissingOp(self)

    def invert(self, lang):
        return self.missing(lang)


def _normalize_where(where, lang=JX):
    if is_many(where):
        where = {"and": where}
    elif not where:
        where = TRUE
    return jx_expression(where, lang)
