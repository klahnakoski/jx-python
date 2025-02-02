# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import Expression
from jx_base.expressions.null_op import NULL
from jx_base.expressions.to_text_op import ToTextOp
from jx_base.language import is_op
from mo_json.types import JX_TEXT, base_type


class IsTextOp(Expression):
    _jx_type = JX_TEXT

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __call__(self, row, rownum=None, rows=None):
        value = self.term(row, rownum, rows)
        if isinstance(value, str):
            return value
        return None

    def __data__(self):
        return {"is_text": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return IsTextOp(self.term.map(map_))

    def missing(self, lang):
        return self.term.missing(lang)

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)
        if is_op(term, IsTextOp) or is_op(term, ToTextOp):
            term = term.term

        if base_type(term.jx_type) == JX_TEXT:
            return term
        elif JX_TEXT in term.jx_type:
            return IsTextOp(term)
        else:
            return NULL
