# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_imports import export

from jx_base.expressions import GetOp, Literal, Variable, FilterOp
from jx_base.utils import delist
from jx_python.streams.expression_factory import ExpressionFactory, factory
from jx_python.streams.typers import Typer, CallableTyper
from mo_json import JxType, JX_IS_NULL, array_of, is_many, JX_ARRAY

_get = object.__getattribute__


class Stream:
    """
    A STREAM OF OBJECTS
    """

    def __init__(self, values, factory, schema):
        self.values = values
        self.factory = factory
        self.schema: JxType = schema

    def __getattr__(self, item):
        return self.map(ExpressionFactory(
            GetOp(self.factory.expr, Literal(item)), self.factory.domain
        ))

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.map(ExpressionFactory(
                GetOp(self.factory.expr, Literal(item)), self.factory.domain
            ))
        if isinstance(item, ExpressionFactory):
            return self.map(ExpressionFactory(
                GetOp(self.factory.expr, item.expr), self.factory.domain
            ))

    def map(self, accessor):
        fact = factory(accessor, self.factory.domain)
        return Stream(self.values, fact, self.schema)

    def filter(self, expr):
        expr = factory(expr).expr
        var = Variable(".", array_of(self.factory.domain.python_type))
        return Stream(
            self.values,
            ExpressionFactory(FilterOp(self.factory.expr, expr), self.factory.domain),
            self.schema,
        )

    ###########################################################################
    # TERMINATORS
    ###########################################################################

    def __iter__(self):
        func = self.factory.build()
        return iter(func(self.values))

    def to_list(self):
        func = self.factory.build()
        return func(self.values)

    def to_value(self):
        func = self.factory.build()
        return delist(func(self.values))


def stream(values):
    typer = Typer(example=values)
    if is_many(values):
        jx_type = JX_ARRAY
    elif values == None:
        jx_type = JX_IS_NULL
        values = []
    else:
        jx_type = array_of(typer.python_type)
        values = [values]

    return Stream(
        values,
        ExpressionFactory(Variable(".", jx_type), typer),
        JX_IS_NULL
    )


ANNOTATIONS = {
    (str, "encode"): CallableTyper(python_type=bytes),
}

export("jx_python.streams.typers", ANNOTATIONS)
export("jx_python.streams.typers", Stream)
