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
from jx_base.expressions.false_op import FALSE
from jx_base.utils import enlist
from mo_dots import exists


class UnionOp(Expression):
    """
    DECISIVE SET UNION: COLLECT THE DISTINCT VALUES OF frum
    """

    def __init__(self, *terms, frum=None):
        if terms:
            frum = terms[0]
        Expression.__init__(self, frum)
        self.frum = frum

    def __call__(self, row, rownum=None, rows=None):
        # A UNION OF COLLECTIONS IS FLAT: A MEMBER THAT IS ITSELF A COLLECTION CONTRIBUTES ITS
        # OWN MEMBERS - AND A set COULD NOT HOLD IT ANYWAY
        values = enlist(self.frum(row, rownum, rows))
        return set(w for v in values for w in enlist(v) if exists(w))

    def __data__(self):
        return {"union": self.frum.__data__()}

    @property
    def jx_type(self):
        return self.frum.jx_type

    def vars(self):
        return self.frum.vars()

    def map(self, map_):
        return UnionOp(frum=self.frum.map(map_))

    def missing(self, lang):
        return FALSE

    def partial_eval(self, lang):
        return lang.UnionOp(frum=self.frum.partial_eval(lang))
