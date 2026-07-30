# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)

from mo_dots import exists

from jx_base.utils import enlist

from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.tally_op import TallyOp
from jx_base.expressions.true_op import TRUE
from mo_json.types import JX_INTEGER


class CountOp(Expression):
    """
    DECISIVE COUNT (SEE TallyOp FOR CONSERVATIVE COUNT)
    """

    has_simple_form = False
    _jx_type = JX_INTEGER

    def __new__(cls, *terms, frum=None):
        if frum is None and len(terms) > 1:
            return TallyOp(*terms, nulls=True)
        # object.__new__(cls), NOT object.__new__(CountOp): THE LANGUAGE-SPECIFIC SUBCLASS MUST
        # SURVIVE, OR partial_eval RETURNS A JX OP TO A lang THAT ASKED FOR ITS OWN
        return object.__new__(cls)

    def __init__(self, *terms, frum=None):
        if terms:
            frum = terms[0]
        Expression.__init__(self, frum)
        self.frum = frum

    def __call__(self, row, rownum=None, rows=None):
        return sum((1 for t in enlist(self.frum(row, rownum, rows)) if exists(t)), 0)

    def __data__(self):
        return {"count": self.frum.__data__()}

    def vars(self):
        return self.frum.vars()

    def join_vars(self):
        return set()  # AN AGGREGATE OVER A COLLECTION BRINGS ITS OWN SOURCE

    def map(self, map_):
        return CountOp(frum=self.frum.map(map_))

    def partial_eval(self, lang):
        return lang.CountOp(frum=self.frum.partial_eval(lang))

    def missing(self, lang):
        return FALSE

    def exists(self):
        return TRUE
