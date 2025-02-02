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
from mo_json import ARRAY
from mo_json.types import array_of, ARRAY_KEY


class ToValueOp(Expression):
    """
    Try to cast the result to a value (or None), not an array
    """

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __data__(self):
        return {"to_value": self.term.__data__()}

    @property
    def jx_type(self):
        if self.term.jx_type == ARRAY:
            return self.term.jx_type[ARRAY_KEY]
        else:
            return array_of(self.term.jx_type)

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return ToValueOp(self.term.map(map_))

    def missing(self, lang):
        return self.term.missing(lang)

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)
        return ToValueOp(term)
