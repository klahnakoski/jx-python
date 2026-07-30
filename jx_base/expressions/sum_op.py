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
from jx_base.utils import enlist
from mo_dots import exists
from mo_json import JX_NUMBER


class SumOp(Expression):
    """
    DECISIVE ADDITION
    """

    has_simple_form = True
    _jx_type = JX_NUMBER

    def __new__(cls, *terms, frum=None):
        if frum is None and len(terms) > 1:
            return AddOp(*terms, nulls=True)
        # object.__new__(cls), NOT object.__new__(SumOp): THE LANGUAGE-SPECIFIC SUBCLASS MUST
        # SURVIVE, OR partial_eval RETURNS A JX OP TO A lang THAT ASKED FOR ITS OWN
        return object.__new__(cls)

    def __init__(self, *terms, frum=None):
        if terms:
            frum = terms[0]
        Expression.__init__(self, frum)
        self.frum = frum

    def __call__(self, row=None, rownum=None, rows=None):
        return sum(v for v in enlist(self.frum(row, rownum, rows)) if exists(v))

    def __data__(self):
        return {"sum": self.frum.__data__()}

    def vars(self):
        return self.frum.vars()

    def join_vars(self):
        return set()  # AN AGGREGATE OVER A COLLECTION BRINGS ITS OWN SOURCE

    def map(self, map_):
        return SumOp(frum=self.frum.map(map_))

    def partial_eval(self, lang):
        return lang.SumOp(frum=self.frum.partial_eval(lang))
