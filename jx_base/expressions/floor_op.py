# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import BaseBinaryOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import ONE
from mo_json.types import JX_NUMBER


class FloorOp(BaseBinaryOp):
    has_simple_form = True
    _jx_type = JX_NUMBER

    def __init__(self, lhs, rhs=ONE):
        Expression.__init__(self, lhs, rhs)
        self.lhs, self.rhs = lhs, rhs
