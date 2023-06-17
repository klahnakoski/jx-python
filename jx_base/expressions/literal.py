# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import Expression
from mo_dots import Null, is_data
from mo_future import is_text
from mo_imports import expect, export
from mo_json import value2json, value_to_jx_type

DateOp, FALSE, TRUE, NULL = expect("DateOp", "FALSE", "TRUE", "NULL")


class Literal(Expression):
    """
    A literal JSON document
    """

    op = "literal"

    def __new__(cls, term):
        if term == None:
            return NULL
        if term is True:
            return TRUE
        if term is False:
            return FALSE
        if term == 0:
            return ZERO
        if term == 1:
            return ONE
        if is_text(term) and not term:
            return NULL
        if is_data(term) and term.get("date"):
            # SPECIAL CASE
            return DateOp(term.get("date"))
        return object.__new__(cls)

    def __init__(self, value):
        Expression.__init__(self)
        self.simplified = True
        self._value = value

    @classmethod
    def define(cls, expr):
        return Literal(expr.get("literal"))

    def __nonzero__(self):
        return True

    def __eq__(self, other):
        if other == None:
            if self._value == None:
                return True
            else:
                return False
        elif self._value == None:
            return False

        if is_literal(other):
            return (self._value == other._value) or (self.json == other.json)

    def __data__(self):
        return {"literal": self.value}

    @property
    def value(self):
        return self._value

    @property
    def json(self):
        if self._value == "":
            self._json = '""'
        else:
            self._json = value2json(self._value)

        return self._json

    def vars(self):
        return set()

    def map(self, map_):
        return self

    def missing(self, lang):
        if self._value in [None, Null]:
            return TRUE
        if self.value == "":
            return TRUE
        return FALSE

    def invert(self, lang):
        return self.missing(lang)

    def __call__(self, row=None, rownum=None, rows=None):
        return self.value

    def __str__(self):
        return self.json

    @property
    def type(self):
        return value_to_jx_type(self._value)

    def partial_eval(self, lang):
        return lang.Literal(self.value)

    def str(self):
        return str(self.value)


ZERO = object.__new__(Literal)
Literal.__init__(ZERO, 0)
ONE = object.__new__(Literal)
Literal.__init__(ONE, 1)
EMPTY_ARRAY = object.__new__(Literal)
Literal.__init__(EMPTY_ARRAY, [])


literal_op_ids = tuple()


def register_literal(op):
    global literal_op_ids
    literal_op_ids = literal_op_ids + (op.get_id(),)


def is_literal(l):
    try:
        return l.get_id() in literal_op_ids
    except Exception:
        return False


export("jx_base.expressions.expression", Literal)
export("jx_base.expressions.expression", is_literal)
export("jx_base.expressions._utils", Literal)
