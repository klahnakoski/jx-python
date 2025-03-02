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
from jx_base.expressions.literal import is_literal, Literal
from mo_json import JxType
from mo_logs import logger


class NameOp(Expression):
    """
    Attach a name to value, or structure
    """

    def __init__(self, frum, name):
        if not is_literal(name):
            logger.error("expecting a literal name")
        Expression.__init__(self, frum, name)
        self.frum = frum
        self._name = name

    @classmethod
    def define(cls, expr):
        frum, name = expr["name"]
        if isinstance(name, str):
            name = Literal(name)
        else:
            name = _jx_expression(name)
        return NameOp(_jx_expression(frum, cls.lang), name)

    def __data__(self):
        return symbiotic(NameOp, self.frum, self._name.__data__())

    def vars(self):
        return self.frum.vars() | self._name.vars()

    def map(self, map_):
        return NameOp(self.frum.map(map_), self._name.map(map_))

    @property
    def jx_type(self):
        return JxType(**{self._name.value: self.frum.jx_type})

    def missing(self, lang):
        return self.frum.missing(lang)
