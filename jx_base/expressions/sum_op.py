# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_logs import logger

from jx_base.expressions.add_op import AddOp

from jx_base.expressions import Expression
from mo_dots import exists
from mo_json import JX_NUMBER


class SumOp(Expression):
    """
    DECISIVE ADDITION
    """
    has_simple_form = True
    _jx_type = JX_NUMBER

    def __new__(cls, *terms, frum=None):
        if frum is not None:
            op = object.__new__(SumOp)
            op.__init__(frum=frum)
            return op
        elif len(terms) > 1:
            return AddOp(*terms, nulls=True)
        else:
            op = object.__new__(SumOp)
            op.__init__(frum=terms[0])
            return op

    def __init__(self, *terms, frum=None):
        if terms:
            frum = terms[0]
        Expression.__init__(self, frum)
        self.frum = frum

    def __call__(self, row=None, rownum=None, rows=None):
        return sum(v for v in self.frum(row, rownum, rows) if exists(v))

    def __data__(self):
        return {"sum": self.frum.__data__()}

    def vars(self):
        return self.frum.vars()

    def map(self, map_):
        return SumOp(frum=self.frum.map(map_))

    def missing(self, lang):
        self.frum.missing(lang)

    def partial_eval(self, lang):
        return SumOp(frum=self.frum.partial_eval(lang))
