# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import mo_json
from jx_base.expressions.coalesce_op import CoalesceOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.first_op import FirstOp
from jx_base.expressions.literal import Literal
from jx_base.expressions.literal import is_literal
from jx_base.expressions.null_op import NULL
from jx_base.language import is_op
from mo_json.types import JX_TEXT, JX_IS_NULL


class ToTextOp(Expression):
    _jx_type = JX_TEXT

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __call__(self, row, rownum=None, rows=None):
        try:
            return str(self.term(row, rownum, rows))
        except:
            return None

    def __data__(self):
        return {"to_text": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return ToTextOp(self.term.map(map_))

    def missing(self, lang):
        return self.term.missing(lang)

    def partial_eval(self, lang):
        term = self.term
        if term.jx_type is JX_IS_NULL:
            return NULL
        term = (FirstOp(term)).partial_eval(lang)
        if is_op(term, ToTextOp):
            return term.term.partial_eval(lang)
        elif is_op(term, CoalesceOp):
            return lang.CoalesceOp(*(ToTextOp(t).partial_eval(lang) for t in term.terms))
        elif term.jx_type == JX_TEXT:
            return term
        elif is_literal(term):
            if term.jx_type == JX_TEXT:
                return term
            else:
                return Literal(mo_json.value2json(term.value))
        return lang.ToTextOp(term)

    def __eq__(self, other):
        if not is_op(other, ToTextOp):
            return False
        return self.term == other.term
