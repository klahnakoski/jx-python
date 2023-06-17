# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from mo_dots import exists

from jx_base.expressions import Expression
from jx_base.expressions.to_array_op import ToArrayOp
from mo_json import JX_NUMBER


class SumOp(Expression):
    """
    DECISIVE ADDITION
    """
    op = "sum"

    has_simple_form = True
    _data_type = JX_NUMBER

    def __init__(self, term):
        """
        EXPECTING AN EXPRESSION THAT RETURNS AN ARRAY TO SUM
        """
        Expression.__init__(self, term)
        self.term = term

    def __call__(self, row=None, rownum=None, rows=None):
        return sum(v for v in self.term(row, rownum, rows) if exists(v))

    def __data__(self):
        return {
            "sum": self.terms.__data__()
        }

    def vars(self):
        return self.terms.vars()

    def map(self, map_):
        return SumOp(self.terms.map(map_))

    def missing(self, lang):
        self.terms.missing(lang)

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)
        return SumOp(term)
