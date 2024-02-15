# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import concat_field
from jx_base.expressions.variable import Variable
from mo_json import JX_ANY, quote


class SqlVariable(Variable):
    simplified = True

    def __init__(self, *es_path, jx_type=JX_ANY):
        self.es_path = es_path
        self._jx_type = jx_type

    def __data__(self):
        return quote(str(self))

    def vars(self):
        return {self}

    def map(self, map_):
        replacement = map_.get(self.var)
        if replacement is None:
            return self
        if isinstance(replacement, str):
            return Variable(replacement)
        else:
            return replacement

    def __hash__(self):
        return (self.es_index, self.es_column).__hash__()

    def __eq__(self, other):
        return isinstance(other, SqlVariable) and self.es_index == other.es_index and self.es_column == other.es_column

    def __str__(self):
        params = [p for p in [self.es_index, self.es_column] if p is not None]
        return concat_field(*params)

    def partial_eval(self, lang):
        return self
