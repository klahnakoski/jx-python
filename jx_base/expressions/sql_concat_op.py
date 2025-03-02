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
from jx_base.expressions.or_op import OrOp
from jx_base.language import is_op
from mo_json.types import JX_TEXT


class SqlConcatOp(Expression):
    """
    conservative string concatenation
    """

    op = "sql.concat"
    _jx_type = JX_TEXT

    def __init__(self, *terms):
        Expression.__init__(self, *terms)
        self.terms = terms

    def __data__(self):
        return {"sql.concat": [t.__data__() for t in self.terms]}

    def missing(self, lang):
        return OrOp(*(t.missing(lang) for t in self.terms))

    def __eq__(self, other):
        if not is_op(other, SqlConcatOp):
            return False
        if len(self.terms) != len(other.terms):
            return False
        return all(t == o for t, o in zip(self.terms, other.terms))

    def partial_eval(self, lang):
        if not self.terms:
            return NULL
        elif len(self.terms) == 1:
            return self.terms[0].partial_eval(lang)
        else:
            return lang.SqlConcatOp(*(t.partial_eval(lang) for t in self.terms))
