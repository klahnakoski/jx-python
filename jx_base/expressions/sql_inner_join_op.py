from dataclasses import dataclass
from typing import List

from jx_base.expressions import Expression
from mo_future import flatten


@dataclass
class SqlJoinOne:
    join: Expression
    on: Expression


class SqlInnerJoinOp(Expression):
    def __init__(self, frum, *joins: List[SqlJoinOne]):
        Expression.__init__(self, frum, *flatten((j.join, j.on) for j in joins))
        self.frum = frum
        self.joins = joins
