# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from typing import List
from dataclasses import dataclass
from jx_base.expressions.expression import Expression


@dataclass
class OneOrder:
    expr: Expression
    direction: str

    def __iter__(self):
        yield from self.expr
        if self.direction:
            yield from self.direction


class SqlOrderByOp(Expression):
    def __init__(self, frum, order: List[OneOrder]):
        Expression.__init__(self, frum, *(o.expr for o in order))
        self.frum = frum
        self.order = order


