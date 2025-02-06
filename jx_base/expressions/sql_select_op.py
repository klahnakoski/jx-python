# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from typing import Tuple, Iterable, Dict

from jx_base.expressions._utils import TYPE_CHECK
from jx_base.expressions import Expression, SelectOne
from jx_base.models.container import Container
from mo_json import union_type
from mo_logs import Log


class SqlSelectOp(Expression):
    has_simple_form = True

    def __init__(self, frum, *terms: Tuple[SelectOne], **kwargs: Dict[str, Expression]):
        """
        :param terms: list OF SelectOne DESCRIPTORS
        """
        if TYPE_CHECK and (
            not all(isinstance(term, SelectOne) for term in terms) or any(term.name is None for term in terms)
        ):
            Log.error("expecting list of SelectOne")
        Expression.__init__(self, frum, *[t.value for t in terms], *kwargs.values())
        self.frum = frum
        self.terms = terms + tuple(*(SelectOne(k, v) for k, v in kwargs.items()))
        self._jx_type = union_type(*(t.name + t.value.jx_type for t in terms))

    @property
    def jx_type(self):
        return union_type(*(t.value.jx_type for t in self.terms))

    def apply(self, container: Container):
        result = self.frum.apply(container)
        return SelectOp(result, *self.terms)

    def __iter__(self) -> Iterable[Tuple[str, Expression, str]]:
        """
        :return:  return iterator of (name, value) tuples
        """
        for term in self.terms:
            yield term.name, term.value

    def __data__(self):
        return {"select": [self.frum.__data__()] + [term.__data__() for term in self.terms]}

    def vars(self):
        return set(v for term in self.terms for v in term.value.vars())

    def map(self, map_):
        return SelectOp(self.frum, *(SelectOne(name, value.map(map_)) for name, value in self))
