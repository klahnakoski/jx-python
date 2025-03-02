# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import operator
from functools import reduce

from mo_dots import exists

from jx_base.expressions.base_multi_op import BaseMultiOp


class MulOp(BaseMultiOp):
    def __call__(self, row=None, rownum=None, rows=None):
        if self.decisive:
            return reduce(operator.mul, (v for t in self.terms for v in [t(row, rownum, rows)] if exists(v)))
        else:
            output = 1
            for t in self.terms:
                v = t(row, rownum, rows)
                if exists(v):
                    output *= v
                else:
                    return None
            return output
