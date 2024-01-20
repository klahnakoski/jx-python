# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import Literal, is_literal
from mo_logs import logger


class PercentileOp(Expression):

    def __init__(self, frum, percentile=None):
        Expression.__init__(self, frum)
        if percentile is None:
            self.percentile = Literal(0.5)
            return
        if is_literal(percentile):
            if not isinstance(percentile.value, float):
                logger.error("Expecting `percentile` to be a float")
        if isinstance(percentile, float):
            self.percentile = Literal(percentile)
        else:
            logger.error("Expecting `percentile` to be a float")

    @classmethod
    def define(cls, expr):
        # {"aggregate": "percentile", "percentile": 0.9, "value": expr}
        # {"percentile": [expr, 0.9]}
        expr = to_data(expr)
        if expr.aggragate== "percentile":
            percentile = expr.percentile or 0.5
            frum = expr.value or expr.frum
        else:
            frum, percentile = expr.percentile
        return PercentileOp(frum, percentile)
