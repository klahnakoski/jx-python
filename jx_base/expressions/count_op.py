# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)

from mo_dots import exists

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
        if frum is not None:
            op = object.__new__(CountOp)
            op.__init__(frum=frum)
            return op
        elif len(terms) > 1:
            return TallyOp(*terms, nulls=True)
        else:
            op = object.__new__(CountOp)
            op.__init__(frum=terms[0])
            return op

    def __init__(self, *terms, frum=None):
        if terms:
            frum = terms[0]
        Expression.__init__(self, frum)
        self.frum = frum

    def __call__(self, row, rownum, rows):
        return sum((1 for t in self.frum(row, rownum, rows) if exists(t)), 0)

    def __data__(self):
        return {"count": self.frum.__data__()}

    def partial_eval(self, lang):
        return lang.CountOp(frum=self.frum.partial_eval(lang))

    def missing(self, lang):
        return FALSE

    def exists(self):
        return TRUE
