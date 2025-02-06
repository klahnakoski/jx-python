# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions.and_op import AndOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.null_op import NULL
from jx_base.expressions.or_op import OrOp
from jx_base.expressions.sql_is_null_op import SqlIsNullOp
from jx_base.expressions.true_op import TRUE
from jx_base.language import is_op
from mo_json.types import JX_BOOLEAN


class SqlOrOp(Expression):
    """
    A CONSERVATIVE OR OPERATION
    """
    _jx_type = JX_BOOLEAN

    def __init__(self, *terms):
        Expression.__init__(self, *terms)
        self.terms = terms

    def __data__(self):
        return {"sql.or": [t.__data__() for t in self.terms]}

    def missing(self, lang):
        # TECHNICALLY NOT CORRECT, ANY TRUE TERM WILL MAKE THE WHOLE THING TRUE, BUT EASIER TO REASON ABOUT
        return OrOp(*(t.missing(lang) for t in self.terms))

    def __eq__(self, other):
        if not is_op(other, SqlOrOp):
            return False
        if len(self.terms) != len(other.terms):
            return False
        return all(t == o for t, o in zip(self.terms, other.terms))

    def partial_eval(self, lang):
        terms = []
        ands = []
        for t in self.terms:
            simple = lang.ToBooleanOp(t).partial_eval(lang)
            if simple is FALSE or simple is NULL:
                continue
            elif simple is TRUE:
                return TRUE
            elif is_op(simple, OrOp):
                terms.extend([tt for tt in simple.terms if tt not in terms])
            elif is_op(simple, AndOp):
                ands.append(simple)
            elif simple not in terms:
                terms.append(simple)

        if ands:  # REMOVE TERMS THAT ARE MORE RESTRICTIVE THAN OTHERS
            for a in ands:
                for tt in a.terms:
                    if tt in terms:
                        break
                else:
                    terms.append(a)

        if len(terms) == 0:
            return FALSE
        if len(terms) == 1:
            return terms[0]
        return lang.OrOp(*terms)
