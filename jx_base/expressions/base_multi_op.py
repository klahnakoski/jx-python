# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from typing import Tuple

from jx_base.expressions._utils import builtin_ops
from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import Literal, ZERO, ONE, is_literal
from jx_base.language import is_op
from mo_imports import expect
from mo_json.types import JX_NUMBER
from mo_logs import logger

AndOp, CoalesceOp, NULL, OrOp, WhenOp, ToNumberOp = expect(
    "AndOp", "CoalesceOp", "NULL", "OrOp", "WhenOp", "ToNumberOp"
)


class BaseMultiOp(Expression):
    """
    conservative eval of multi-operand operators
    """
    has_simple_form = True
    _jx_type = JX_NUMBER

    def __init__(self, *terms: Tuple[Expression], nulls=False):
        if nulls is None:
            logger.error("nulls must be specified")
        Expression.__init__(self, *terms)
        self.terms = terms
        self.decisive = nulls
        self.simplified = False

    def __eq__(self, other):
        if not is_op(other, self.__class__):
            return False
        if len(self.terms) != len(other.terms):
            return False
        return all(s == o for s, o in zip(self.terms, other.terms))

    def __data__(self):
        return {self.op: [t.__data__() for t in self.terms], "nulls": self.decisive}

    def vars(self):
        output = set()
        for t in self.terms:
            output |= t.vars()
        return output

    def map(self, map_):
        return self.__class__(*(t.map(map_) for t in self.terms), null=self.decisive)

    def missing(self, lang):
        if self.decisive:
            return AndOp(*(t.missing(lang) for t in self.terms))
        else:
            return OrOp(*(t.missing(lang) for t in self.terms))

    def partial_eval(self, lang):
        literal_acc = None
        terms = []
        for t in self.terms:
            simple = t.partial_eval(lang)
            if simple is NULL:
                if self.decisive:
                    pass
                else:
                    return NULL
            elif is_literal(simple):
                if literal_acc is None:
                    literal_acc = simple.value
                else:
                    literal_acc = builtin_ops[self.op](literal_acc, simple.value)
            else:
                terms.append(simple)

        if len(terms) == 0:
            return Literal(literal_acc)
        elif len(terms) == 1 and literal_acc is None:
            return terms[0]
        else:
            if literal_acc is not None:
                terms.append(Literal(literal_acc))
            return getattr(lang, self.__class__.__name__)(*terms, nulls=self.decisive)


_jx_identity = {"add": ZERO, "mul": ONE, "cardinality": ZERO, "sum": ZERO, "product": ONE}
