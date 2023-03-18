# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from mo_dots import exists
from mo_future import sort_using_cmp
from mo_imports import export

from jx_base.expressions import GetOp, Literal, Variable, FilterOp, SelectOp
from jx_base.expressions.select_op import SelectOne
from jx_base.language import value_compare
from jx_base.utils import delist, enlist
from jx_python.expressions.get_op import get_attr
from jx_python.streams.expression_factory import ExpressionFactory, factory, it
from jx_python.streams.typers import Typer, CallableTyper
from jx_python.utils import distinct, group
from mo_json.types import _A

_get = object.__getattribute__
row = Variable(".")


class Stream:
    """
    A STREAM OF OBJECTS
    """

    __slots__ = ["factory", "values"]

    def __init__(self, values, factory: ExpressionFactory):
        if not isinstance(factory, ExpressionFactory):
            raise Exception("not allowed")
        self.values = values
        self.factory = factory

    def __getattr__(self, item):
        if item in Stream.__slots__:
            return None

        print(item)
        accessor = ExpressionFactory(GetOp(self.factory.expr, Literal(item)))
        fact = factory(accessor)
        return Stream(self.values, fact)

    def __getitem__(self, item):
        if isinstance(item, str):
            accessor = ExpressionFactory(GetOp(self.factory.expr, Literal(item)))
        else:
            accessor = ExpressionFactory(GetOp(self.factory.expr, factory(item)))
        fact = factory(accessor)
        return Stream(self.values, fact)

    def __iter__(self):
        func = self.factory.build()
        return iter(func(self.values))

    def map(self, accessor):
        accessor = factory(accessor)
        fact = ExpressionFactory(SelectOp(self.factory.expr, (SelectOne(".", accessor.expr),)))
        return Stream(self.values, fact)

    def filter(self, expr):
        expr = factory(expr).expr
        return Stream(self.values, ExpressionFactory(FilterOp(self.factory.expr, expr)),)

    def distinct(self):
        return Stream(distinct(self), ExpressionFactory(Variable(".")),)

    def reverse(self):
        return Stream(list(reversed(list(self))), ExpressionFactory(Variable(".")),)

    def sort(self):
        return Stream(list(sort_using_cmp(self, value_compare)), ExpressionFactory(Variable(".")),)

    def limit(self, num):
        def limit():
            for i, v in enumerate(self):
                if i >= num:
                    break
                yield v

        return Stream(list(limit()), ExpressionFactory(Variable(".")),)

    def group(self, expr):
        fact = factory(expr)
        func = fact.build()
        sub_factory = ExpressionFactory(Variable("."))
        this = self

        def nested():
            for g, rows in group(this, func):
                yield {
                    _A: Stream(list(rows), sub_factory),
                    "group": g,
                }

        return Stream(list(nested()), ExpressionFactory(Variable(".")))

    ###########################################################################
    # TERMINATORS
    ###########################################################################

    def to_list(self):
        row0 = self.values
        result = [
            get_attr(row1, "props", "a")
            for rows1 in [get_attr(enlist(row0), "value")]
            for rownum1, row1 in enumerate(rows1)
        ]

        func = self.factory.build()
        return func(self.values)

    def to_value(self):
        func = self.factory.build()
        return delist(func(self.values))

    def sum(self):
        return sum(v for v in self if exists(v))

    def first(self):
        func = self.factory.first().build()
        return func(self.values)

    def last(self):
        func = self.factory.last().build()
        return func(self.values)


def stream(values):
    return Stream(values, ExpressionFactory(SelectOp(it.expr, (SelectOne(".", Variable(".")),))))


ANNOTATIONS = {
    (str, "encode"): CallableTyper(python_type=bytes),
}

export("jx_python.streams.typers", ANNOTATIONS)
export("jx_python.streams.typers", Stream)
