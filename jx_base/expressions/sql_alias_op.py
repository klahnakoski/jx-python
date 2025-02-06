# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import Expression, Literal
from jx_base.language import is_op


class SqlAliasOp(Expression):
    """
    MUCH LIKE NameOp, BUT FOR SQL
    """

    def __init__(self, value, name: str):
        if "SQL" not in get_class_names(value.__class__):
            raise ValueError(f"Expected SQL, but got {value}")
        Expression.__init__(self, value, Literal(name))
        self.value = value
        self.name = name
        self._jx_type = self.name + self.value.jx_type

    def __data__(self):
        return {self.name: self.value.__data__()}

    def missing(self, lang):
        return self.value.missing(lang)

    def __eq__(self, other):
        if not is_op(other, SqlAliasOp):
            return False
        return self.name == other.name and self.value == other.value

    def __repr__(self):
        return f"SqlAliasOp({self.name}={self.value})"


def get_class_names(cls):
    yield cls.__name__
    for base_class in cls.__bases__:
        yield from get_class_names(base_class)
