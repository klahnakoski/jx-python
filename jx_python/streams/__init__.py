# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import unwraplist
from mo_files import File
from mo_imports import export
from mo_streams import ByteStream
from mo_streams.utils import File_usingStream

from mo_json import JxType, JX_IS_NULL

from jx_base.expressions import GetOp, Literal, Variable, FilterOp
from jx_python.streams.expression_factory import ExpressionFactory, factory
from jx_python.streams.typers import Typer, CallableTyper

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
        return ExpressionFactory(
            FilterOp(self.values, expr), self.factory.domain
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
        return unwraplist(func(self.values))


def stream(values):
    return Stream(
        values, ExpressionFactory(Variable("."), Typer(example=values)), JX_IS_NULL
    )


ANNOTATIONS = {
    (str, "encode"): CallableTyper(python_type=bytes),
}

export("jx_python.streams.typers", ANNOTATIONS)
export("jx_python.streams.typers", Stream)
