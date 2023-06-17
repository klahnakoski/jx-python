# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from typing import Tuple

from jx_base.expressions._utils import builtin_ops, operators
from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import Literal, ZERO, ONE, is_literal
from jx_base.expressions.true_op import TRUE
from mo_imports import expect
from mo_json.types import JX_NUMBER

AndOp, CoalesceOp, NULL, OrOp, WhenOp, ToNumberOp = expect(
    "AndOp", "CoalesceOp", "NULL", "OrOp", "WhenOp", "ToNumberOp"
)


class BaseMultiOp(Expression):
    has_simple_form = True
    _data_type = JX_NUMBER

    def __init__(self, *terms, nulls=False, **clauses):
        Expression.__init__(self, *terms)
        self.terms: Tuple[Expression] = terms
        # decisive==True WILL HAVE OP RETURN null ONLY IF ALL OPERANDS ARE null
        self.decisive = nulls in (True, TRUE)

    def __data__(self):
        return {
            self.op: [t.__data__() for t in self.terms],
            "decisive": self.decisive,
        }

    def vars(self):
        output = set()
        for t in self.terms:
            output |= t.vars()
        return output

    def map(self, map_):
        return self.__class__([t.map(map_) for t in self.terms], **{"decisive": self.decisive})

    def missing(self, lang):
        if self.decisive:
            return AndOp(*(t.missing(lang) for t in self.terms))
        else:
            return OrOp(*(t.missing(lang) for t in self.terms))

    def exists(self):
        if self.decisive:
            return OrOp(*(t.exists() for t in self.terms))
        else:
            return AndOp(*(t.exists() for t in self.terms))

    def partial_eval(self, lang):
        literal_acc = None
        terms = []
        for t in self.terms:
            simple = ToNumberOp(t).partial_eval(lang)
            if simple is NULL:
                pass
            elif is_literal(simple):
                if literal_acc is None:
                    literal_acc = simple.value
                else:
                    literal_acc = builtin_ops[self.op](literal_acc, simple.value)
            else:
                terms.append(simple)

        lang = self.lang
        if len(terms) == 0:
            return Literal(literal_acc)
        elif len(terms) == 1 and literal_acc is None:
            return terms[0]
        elif self.decisive:
            # DECISIVE
            if literal_acc is not None:
                terms.append(Literal(literal_acc))

            output = WhenOp(
                AndOp(*(t.missing(lang) for t in terms)),
                **{"else": operators["basic." + self.op](*(
                    CoalesceOp(t, _jx_identity.get(self.op, NULL)) for t in terms
                ))}
            ).partial_eval(lang)
        else:
            # CONSERVATIVE
            if literal_acc is not None:
                terms.append(Literal(literal_acc))

            output = WhenOp(
                OrOp(*(t.missing(lang) for t in terms)),
                **{"else": operators["basic." + self.op](terms)}
            ).partial_eval(lang)

        return output


_jx_identity = {"add": ZERO, "mul": ONE, "cardinality": ZERO, "sum": ZERO, "product": ONE}
