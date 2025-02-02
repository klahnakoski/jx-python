# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions._utils import _jx_expression, symbiotic
from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import Literal
from jx_base.models.container import Container
from jx_base.utils import Log


class CommentOp(Expression):
    def __init__(self, frum, comment):
        Expression.__init__(self, frum, comment)
        self.frum = frum
        self.comment = comment

    @classmethod
    def define(cls, expr):
        items = list(expr.items())
        if len(items) != 1:
            Log.error("expecting comment")
        op, (frum, comment) = items[0]
        if op not in ["comment", "description", "meta"]:
            Log.error("expecting comment")
        return cls.lang.CommentOp(_jx_expression(frum, cls.lang), Literal(comment))

    def apply(self, container: Container):
        # TODO: ADD COMMENT TO RESULT
        result = self.frum.apply(container)
        result.comment = self.comment.value
        return result

    def __data__(self):
        symbiotic(CommentOp, self.frum, self.comment.__data__())

    def vars(self):
        return self.frum.vars() | self.comment.vars()

    def map(self, map_):
        return CommentOp(self.frum.map(mao_), self.comment.map(map_))

    @property
    def jx_type(self):
        return self.frum.jx_type
