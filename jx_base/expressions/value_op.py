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
from mo_imports import expect
from mo_json import JX_ANY


class ValueOp(Expression):
    """
    A NO-OP FOR SYMBIOTIC FUNCTIONS
    """
    _jx_type = JX_ANY

    def __init__(self, value):
        Expression.__init__(self, value)
        self.value = value

    @property
    def schema(self):
        return self.value.schema

    def vars(self):
        return self.value.vars()

    def map(self, map_):
        return ValueOp(self.value.map(map_))

    def missing(self, lang):
        return self.value.missing(lang)
