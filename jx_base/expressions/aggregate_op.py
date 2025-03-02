# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_logs import logger

from jx_base.expressions.expression import Expression
from jx_base.expressions.null_op import NULL
from jx_base.expressions.all_op import AllOp
from jx_base.expressions.any_op import AnyOp
from mo_future import first
from mo_imports import DelayedValue


class AggregateOp(Expression):
    def __init__(self, frum, op, **options):
        logger.error("general aggregate not supported")

    def apply(self, container):
        source = self.frum.apply(container)
        return source.query(self.op)

    def __data__(self):
        return {"aggregate": [self.frum.__data__(), first(self.op(NULL).__data__().keys())]}

    def vars(self):
        return self.frum.vars() | self.op.vars()

    def map(self, map_):
        return AggregateOp(self.frum.map(map_), self.op.map(map_))

    @property
    def jx_type(self):
        # THIS CAN BE BETTER
        return self.frum.jx_type

    def missing(self, lang):
        return self.frum.missing()

    def invert(self, lang):
        return self.missing(lang)


def canonical_aggregates():
    from jx_base.expressions.avg_op import AvgOp
    from jx_base.expressions.cardinality_op import CardinalityOp
    from jx_base.expressions.count_op import CountOp
    from jx_base.expressions.max_op import MaxOp
    from jx_base.expressions.min_op import MinOp
    from jx_base.expressions.null_op import NullOp
    from jx_base.expressions.percentile_op import PercentileOp
    from jx_base.expressions.union_op import UnionOp
    from jx_base.expressions.sum_op import SumOp

    lookup = {
        "cardinality": CardinalityOp,
        "count": CountOp,
        "min": MinOp,
        "minimum": MinOp,
        "percentile": PercentileOp,
        "max": MaxOp,
        "maximum": MaxOp,
        "add": SumOp,
        "sum": SumOp,
        "avg": AvgOp,
        "average": AvgOp,
        "mean": AvgOp,
        "union": UnionOp,
        "any": AnyOp,
        "all": AllOp,
        "or": AnyOp,
        "and": AllOp,
    }
    for _, v in list(lookup.items()):
        lookup[v] = v
    return lookup


canonical_aggregates = DelayedValue(canonical_aggregates)
