# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.eq_op import EqOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.find_op import FindOp
from jx_base.expressions.literal import Literal
from jx_base.expressions.literal import is_literal
from jx_base.expressions.or_op import OrOp
from jx_base.expressions.script_op import ScriptOp
from jx_base.expressions.true_op import TRUE
from jx_base.expressions.variable import is_variable


class SplitOp(Expression):
    has_simple_form = True

    def __init__(self, *term, **kwargs):
        Expression.__init__(self, *term)
        self.value, self.find = term

    def __data__(self):
        if is_variable(self.value) and is_literal(self.find):
            return {"split": {self.value.var: self.find.value}}
        else:
            return {"split": [self.value.__data__(), self.find.__data__()]}

    def vars(self):
        return self.value.vars() | self.find.vars() | self.default.vars() | self.start.vars()

    def map(self, map_):
        return FindOp(
            [self.value.map(map_), self.find.map(map_)], start=self.start.map(map_), default=self.default.map(map_),
        )

    def missing(self, lang):
        v = self.value.to_es_script(not_null=True)
        find = self.find.to_es_script(not_null=True)
        index = v + ".indexOf(" + find + ", " + self.start.to_es_script() + ")"

        return lang.AndOp(
            self.default.missing(lang),
            OrOp(self.value.missing(lang), self.find.missing(lang), EqOp(ScriptOp(index), Literal(-1)),),
        )

    def exists(self):
        return TRUE
