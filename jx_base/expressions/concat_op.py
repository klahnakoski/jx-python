# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#


from jx_base.expressions._utils import jx_expression
from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import Literal
from jx_base.expressions.literal import is_literal
from jx_base.expressions.null_op import NULL
from jx_base.expressions.variable import Variable, is_variable
from jx_base.utils import is_variable_name
from mo_dots import is_data, is_many
from mo_future import first, is_text
from mo_json.types import JX_TEXT
from mo_logs import Log


class ConcatOp(Expression):
    has_simple_form = True
    _jx_type = JX_TEXT

    def __init__(self, *terms, separator=Literal("")):
        if not is_many(terms):
            Log.error("Expecting many terms")
        if not is_literal(separator):
            Log.error("Expecting a literal separator")
        Expression.__init__(self, *terms, separator)
        self.terms = terms
        self.separator = separator

    @classmethod
    def define(cls, expr):
        terms = expr["concat"]
        if is_data(terms):
            k, v = first(terms.items())
            terms = [Variable(k), Literal(v)]
        else:
            terms = [jx_expression(t) for t in terms]

        return ConcatOp(
            *terms,
            **{
                k: Literal(v) if is_text(v) and not is_variable_name(v) else jx_expression(v)
                for k, v in expr.items()
                if k in ["separator"]
            }
        )

    def partial_eval(self, lang):
        terms = []
        for t in self.terms:
            tt = t.partial_eval(lang)
            if tt is not NULL:
                terms.append(tt)

        if terms:
            return ConcatOp(*terms, separator=self.separator)
        elif len(terms) == 1:
            return terms[0]
        else:
            return NULL

    def __data__(self):
        terms = self.terms
        if len(terms) == 0:
            return NULL
        if len(terms) == 2 and is_variable(terms[0]) and is_literal(terms[1]):
            output = {"concat": {terms[0].var: terms[1].value}}
        else:
            output = {"concat": [t.__data__() for t in terms]}
        if self.separator.json != '""':
            output["separator"] = self.separator.__data__()
        return output

    def invert(self, lang):
        return self.missing(lang)

    def vars(self):
        if not self.terms:
            return set()
        return set.union(*(t.vars() for t in self.terms))

    def map(self, map_):
        return ConcatOp(*[t.map(map_) for t in self.terms], separator=self.separator.map(map_))

    def missing(self, lang):
        return lang.AndOp(*(t.missing(lang) for t in self.terms)).partial_eval(lang)
