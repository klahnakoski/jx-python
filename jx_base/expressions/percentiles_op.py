# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import Literal, is_literal
from mo_dots import listwrap
from mo_logs import logger


class PercentilesOp(Expression):
    """
    ONE OR MORE PERCENTILES OF `frum`.  MEDIAN IS THE 0.5 PERCENTILE, WHICH IS
    THE DEFAULT WHEN NO PERCENTILE IS GIVEN.
    """

    def __init__(self, frum, percentile=None, percentiles=None):
        Expression.__init__(self, frum)
        self.frum = frum
        raw = percentiles if percentiles is not None else percentile
        if raw is None:
            self.percentiles = [Literal(0.5)]  # MEDIAN
            return
        self.percentiles = [_as_percentile(p) for p in listwrap(raw)]

    def __data__(self):
        return {
            "percentiles": self.frum.__data__(),
            "percentile": [p.value for p in self.percentiles],
        }


def _as_percentile(p):
    if is_literal(p):
        if not isinstance(p.value, float):
            logger.error("Expecting `percentile` to be a float")
        return p
    if isinstance(p, float):
        return Literal(p)
    logger.error("Expecting `percentile` to be a float")
