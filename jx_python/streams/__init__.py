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
from jx_base.utils import delist
from jx_python.streams.expression_factory import ExpressionFactory, factory, it
from jx_python.streams.typers import Typer, CallableTyper
from jx_python.utils import distinct, group
from mo_json import JxType, JX_IS_NULL, array_of, is_many
from mo_json.types import _A, JX_ANY

_get = object.__getattribute__
row = Variable(".")


class Stream:
    """
    A STREAM OF OBJECTS
    """

    def __init__(self, values, factory):
        self.values = values
        self.factory = factory

    def __getattr__(self, item):
        accessor = ExpressionFactory(
            GetOp(self.factory.expr, Literal(item)), self.factory.codomain
        )
        fact = factory(accessor, self.factory.codomain[item])
        return Stream(self.values, fact)

    def __getitem__(self, item):
        if isinstance(item, str):
            accessor = ExpressionFactory(
                GetOp(self.factory.expr, Literal(item)), self.factory.codomain
            )
        if isinstance(item, ExpressionFactory):
            accessor = ExpressionFactory(
                GetOp(self.factory.expr, item.expr), self.factory.codomain
            )
        fact = factory(accessor, self.factory.codomain)
        return Stream(self.values, fact)

    def __iter__(self):
        func = self.factory.build()
        return iter(func(self.values))

    def map(self, accessor):

        # Stream(v).filter()...
        # Stream(v).map(it.filter())...
        # it.filter()... .__call__(v)


        accessor = factory(accessor, self.factory.codomain)
        fact = ExpressionFactory(
            SelectOp(self.factory.expr, (SelectOne(".", accessor.expr),)),
            self.factory.codomain,
        )
        return Stream(self.values, fact)

    def filter(self, expr):
        expr = factory(expr).expr
        return Stream(
            self.values,
            ExpressionFactory(FilterOp(self.factory.expr, expr), self.factory.codomain),
        )

    def distinct(self):
        return Stream(
            distinct(self),
            ExpressionFactory(Variable("."), self.factory.typer),
        )

    def reverse(self):
        return Stream(
            list(reversed(list(self))),
            ExpressionFactory(Variable("."), self.factory.typer),
        )

    def sort(self):
        return Stream(
            list(sort_using_cmp(self, value_compare)),
            ExpressionFactory(Variable("."), self.factory.typer),
        )

    def limit(self, num):
        def limit():
            for i, v in enumerate(self):
                if i >= num:
                    break
                yield v

        return Stream(
            list(limit()),
            ExpressionFactory(Variable("."), self.factory.typer),
        )

    def group(self, expr):
        fact = factory(expr)
        sup_codomain = Typer(
            python_type=array_of(self.factory.codomain.python_type)
            | JxType(group=fact.codomain.python_type)
        )
        func = fact.build()
        sub_factory = ExpressionFactory(
            Variable(".", self.factory.codomain.python_type), self.factory.codomain
        )
        this = self

        def nested():
            for g, rows in group(this, func):
                yield {
                    _A: Stream(
                        list(rows), sub_factory, array_of(this.factory.codomain)
                    ),
                    "group": g,
                }

        return Stream(
            list(nested()),
            ExpressionFactory(
                Variable(".", sup_codomain.python_type), Typer(array_of=sup_codomain)
            ),
        )

    ###########################################################################
    # TERMINATORS
    ###########################################################################

    def to_list(self):
        func = self.factory.build()
        return func(self.values)

    def to_value(self):
        func = self.factory.build()
        return delist(func(self.values))

    def sum(self):
        return sum(v for v in self if exists(v))

    def first(self):
        func = self.factory.build()
        for v in self.values:
            return func(v, 0, self.values)
        return None

    def last(self):
        func = self.factory.build()
        values = (
            self.values if isinstance(self.values, (tuple, list)) else list(self.values)
        )
        if self.values:
            return func(values[-1], len(values) - 1, values)
        return None


def stream(values):
    if values == None:
        typer = Typer(python_type=JX_IS_NULL)
        return Stream([], ExpressionFactory(Variable(".", JX_IS_NULL), typer))

    if is_many(values):
        typer = Typer(python_type=array_of(JX_ANY))
    else:
        typer = Typer(example=values)
        values = [values]

    return Stream(
        values,
        it,
    )


ANNOTATIONS = {
    (str, "encode"): CallableTyper(python_type=bytes),
}

export("jx_python.streams.typers", ANNOTATIONS)
export("jx_python.streams.typers", Stream)
