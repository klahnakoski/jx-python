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


class ArrayOfOp(Expression):
    """
    Wrap the term in an array, even if it is an array (for use translating to python)
    """

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __data__(self):
        return {"array_of": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return ArrayOfOp(self.term.map(map_))

    def missing(self, lang):
        return self.term.missing(lang)

    def partial_eval(self, lang):
        return ArrayOfOp(self.term.partial_eval(lang))
