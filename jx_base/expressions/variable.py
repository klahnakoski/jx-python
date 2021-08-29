# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import absolute_import, division, unicode_literals

from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.language import is_op
from jx_base.utils import get_property_name
from mo_dots import is_sequence, split_field
from mo_dots.lists import last
from mo_future import is_text
from mo_imports import export
from mo_json.typed_encoder import inserter_type_to_json_type
from mo_json.types import ToJsonType, JsonType


class Variable(Expression):
    def __init__(self, var, type=None):
        """
        :param var:   DOT DELIMITED PATH INTO A DOCUMENT
        :param type:  JSON TYPE, IF KNOWN
        """
        Expression.__init__(self, None)

        self.var = get_property_name(var)

        if type == None:
            # MAYBE THE NAME HAS A HINT TO THE TYPE
            self.data_type = ToJsonType(inserter_type_to_json_type.get(last(split_field(var))))
        else:
            self.data_type = ToJsonType(type)
        if not isinstance(self.data_type, JsonType):
            Log.error("expecting json type")

    def __call__(self, row, rownum, rows):
        path = split_field(self.var)
        for p in path:
            row = row.get(p)
            if row is None:
                return None
        if is_sequence(row) and len(row) == 1:
            return row[0]
        return row

    def __data__(self):
        return self.var

    def vars(self):
        return {self}

    def map(self, map_):
        replacement = map_.get(self.var)
        if replacement != None:
            if is_text(replacement):
                return Variable(replacement)
            else:
                return replacement
        else:
            return self

    def __hash__(self):
        return self.var.__hash__()

    def __eq__(self, other):
        if is_op(other, Variable):
            return self.var == other.var
        elif is_text(other):
            return self.var == other
        return False

    def __unicode__(self):
        return self.var

    def __str__(self):
        return str(self.var)

    def missing(self, lang):
        if self.var == "_id":
            return FALSE
        else:
            return lang.MissingOp(self)


IDENTITY = Variable(".")

export("jx_base.expressions._utils", Variable)
export("jx_base.expressions.expression", Variable)
export("jx_base.expressions.base_binary_op", Variable)
export("jx_base.expressions.basic_in_op", Variable)
