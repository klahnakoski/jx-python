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
from jx_base.language import is_op
from jx_base.expressions.or_op import OrOp
from mo_json.types import JX_BOOLEAN


class SqlAndOp(Expression):
    _data_type = JX_BOOLEAN

    def __init__(self, *terms):
        Expression.__init__(self, *terms)
        self.terms = terms

    def __data__(self):
        return {"sql.and": [t.__data__() for t in self.terms]}

    def missing(self, lang):
        # TECHNICALLY NOT CORRECT, ANY FALSE TERM WILL MAKE THE WHOLE THING FALSE, BUT EASIER TO REASON ABOUT
        return OrOp(*(t.missing(lang) for t in self.terms))

    def __eq__(self, other):
        if not is_op(other, SqlAndOp):
            return False
        if len(self.terms) != len(other.terms):
            return False
        return all(t==o for t, o in zip(self.terms, other.terms))
