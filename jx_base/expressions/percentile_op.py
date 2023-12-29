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
    op = "percentile"

    def __init__(self, frum, percentile=None):
        BaseMultiOp.__init__(self, frum=frum)
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
