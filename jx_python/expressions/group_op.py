# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import itertools

from mo_dots import is_data
from mo_future import sort_using_cmp

from jx_base.expressions import GroupOp as GroupOp_, ToArrayOp
from jx_base.expressions.python_script import PythonScript
from jx_base.language import value_compare
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json.types import JxType, array_of


class GroupOp(GroupOp_):
    def to_python(self, loop_depth=0):
        frum = self.frum.partial_eval(Python).to_python(loop_depth)
        group = self.group.partial_eval(Python).to_python(loop_depth)

        return PythonScript(
            merge_locals(frum.locals, group.locals, groupby=groupby),
            loop_depth,
            array_of(frum.type) | JxType(group=group.type),
            f"""list(groupby({frum.source}, {group.source}))""",
            self,
        )


def groupby(values, func):
    cmp = lambda a, b: value_compare(func(a), func(b))
    for g, rows in itertools.groupby(sort_using_cmp(values, cmp=cmp), func):
        row = list(rows)
        if is_data(g):
            for k, v in g:
                setattr(row, k, v)
            yield row
        else:
            yield row
