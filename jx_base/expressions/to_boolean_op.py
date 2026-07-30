# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions.expression import Expression, FALSE, TRUE
from mo_dots import exists
from mo_imports import export
from mo_json import JX_BOOLEAN


class ToBooleanOp(Expression):
    """
    CONVERT VALUE TO BOOLEAN, OR KEEP AS BOOLEAN
    """

    _jx_type = JX_BOOLEAN

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __call__(self, row, rownum=None, rows=None):
        v = self.term(row, rownum, rows)
        return exists(v) and v is not False

    def __data__(self):
        return {"boolean": self.term.__data__()}

    def __eq__(self, other):
        return isinstance(other, ToBooleanOp) and self.term == other.term

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return ToBooleanOp(self.term.map(map_))

    def missing(self, lang):
        # A COERCION TO BOOLEAN IS NEVER NULL: `exists(v) and v is not False` (SEE __call__).
        # RETURNING term.missing() MADE EVERY PREDICATE BUILT ON IT NULLABLE, WHICH BREAKS THE
        # SqlScript INVARIANT THAT A `miss` IS NOT ITSELF MISSING
        return FALSE

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)
        if term.jx_type == JX_BOOLEAN or term.missing(lang) is TRUE:
            return term
        elif term is self.term:
            return self
        return ToBooleanOp(term)


export("jx_base.expressions.and_op", ToBooleanOp)
