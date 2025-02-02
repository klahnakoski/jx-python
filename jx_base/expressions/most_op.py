# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.base_multi_op import BaseMultiOp


class MostOp(BaseMultiOp):
    """
    CONSERVATIVE MAXIMUM (SEE MaxOp FOR DECISIVE MAXIMUM)
    """
    def __call__(self, row, rownum=None, rows=None):
        maxi = None
        for t in self.terms:
            v = t(row, rownum, rows)
            if v is None:
                if self.decisive:
                    continue
                else:
                    return None
            if maxi is None:
                maxi = v
            elif v > maxi:
                maxi = v
        return maxi
