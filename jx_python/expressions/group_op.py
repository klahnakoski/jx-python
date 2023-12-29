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
from mo_json.typed_object import TypedObject

from jx_base.expressions import GroupOp as _GroupOp, ToArrayOp
from jx_base.expressions.python_script import PythonScript
from jx_base.language import value_compare
from jx_base.utils import enlist
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_future import sort_using_cmp
from mo_json.typed_encoder import detype
from mo_json.types import JxType, array_of, ARRAY_KEY

ARRAY_KEY = ARRAY_KEY


class GroupOp(_GroupOp):
    def to_python(self, loop_depth=0):
        frum = ToArrayOp(self.frum).partial_eval(Python).to_python(loop_depth)
        group = self.group.partial_eval(Python).to_python(loop_depth)

        return PythonScript(
            merge_locals(frum.locals, group.locals, groupby=groupby, enlist=enlist),
            loop_depth,
            array_of(frum.jx_type) | JxType(group=group.jx_type),
            f"""groupby({frum.source}, lambda row{loop_depth}: {group.source})""",
            self,
        )


def groupby(values, func):
    output = []
    cmp = lambda a, b: value_compare(detype(func(a)), detype(func(b)))
    for g, rows in itertools.groupby(sort_using_cmp(values, cmp=cmp), func):
        row = list(rows)
        if is_data(g):
            output.append(TypedObject(row, **g))
        else:
            output.append(TypedObject(row, group=g))
    return output
