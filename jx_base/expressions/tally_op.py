# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
from jx_base.expressions.base_multi_op import BaseMultiOp
from mo_dots import is_missing


class TallyOp(BaseMultiOp):
    """
    CONSERVATIVE COUNT (SEE CountOp FOR DECISIVE COUNT)
    """

    has_simple_form = False

    def __call__(self, row, rownum=None, rows=None):
        total = 0
        for t in self.terms:
            v = t(row, rownum, rows)
            if is_missing(v):
                if self.decisive:
                    continue
                return None
            total += 1  # count existing values, not their sum
        return total
