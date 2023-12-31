# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
from mo_dots import is_missing

from jx_base.expressions.base_multi_op import BaseMultiOp
from jx_base.expressions.false_op import FALSE
from mo_json.types import JX_INTEGER


class TallyOp(BaseMultiOp):
    """
    CONSERVATIVE COUNT (SEE CountOp FOR DECISIVE COUNT)
    """

    has_simple_form = False
    _jx_type = JX_INTEGER

    def __init__(self, *terms, nulls=None):
        BaseMultiOp.__init__(self, *terms, nulls=nulls)

    def __call__(self, row, rownum, rows):
        total = 0
        for t in self.terms:
            v = t(row, rownum, rows)
            if is_missing(v):
                return None
            total += v
        return total

    def __data__(self):
        return {"tally": [t.__data__() for t in self.terms]}

    def missing(self, lang):
        return FALSE

    def partial_eval(self, lang):
        return lang.TallyOp(*(t.partial_eval(lang) for t in self.terms), nulls=self.decisive)
