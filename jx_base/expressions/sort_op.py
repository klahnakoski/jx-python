# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from typing import List

from jx_base.expressions._utils import jx_expression, _jx_expression
from jx_base.expressions.expression import Expression
from jx_base.utils import enlist
from mo_dots import coalesce
from mo_future import is_text


class SortOne:
    def __init__(self, expr, direction):
        self.expr = expr
        self.direction = direction




class SortOp(Expression):

    def __init__(self, frum, *sorts):
        Expression.__init__(self, frum)
        for s in sorts:
            if not isinstance(s, SortOne):
                raise ValueError("Expecting SortOne")
        self.frum = frum
        self.sorts = sorts

    @classmethod
    def define(cls, expr):
        raw_frum,  *raw_sorts = expr["sort"]
        frum = _jx_expression(raw_frum, cls.lang)
        sorts = _normalize_sort(*raw_sorts)
        return SortOp(frum, *sorts)


def _normalize_sort(sort=None) -> List[SortOne]:
    """
    CONVERT SORT PARAMETERS TO A NORMAL FORM SO EASIER TO USE
    """
    output = []
    for s in enlist(sort):
        if is_text(s):
            output.append(SortOne(jx_expression(s), 1))
        elif is_expression(s):
            output.append(SortOne(s, 1))
        elif mo_math.is_integer(s):
            output.append(SortOne(jx_expression({"offset": s}), 1))
        elif not s.get("sort") and not s.get("value"):
            # {field: direction} format:  eg {"machine_name": "desc"}
            if all(d in sort_direction for d in s.values()):
                for v, d in s.items():
                    output.append(SortOne(
                        jx_expression(v),
                        sort_direction[d]
                    ))
            else:
                Log.error("`sort` clause must have a `value` property")
        else:
            output.append(SortOne(
                jx_expression(coalesce(s.get("value"), s.get("field"))),
                sort_direction[s.get("sort")]
            ))
    return output


sort_direction = {
    "asc": 1,
    "ascending": 1,
    "desc": -1,
    "descending": -1,
    "none": 0,
    1: 1,
    0: 0,
    -1: -1,
    None: 1,
}

