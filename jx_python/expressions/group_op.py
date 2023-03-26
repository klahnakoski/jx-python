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

from jx_base.expressions import GroupOp as GroupOp_
from jx_base.expressions.python_script import PythonScript
from jx_base.utils import enlist
from jx_python import stream
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json.types import _A, JxType, array_of


class GroupOp(GroupOp_):
    def to_python(self, loop_depth=0):
        frum = self.frum.partial_eval(Python).to_python(loop_depth)
        loop_depth = frum.loop_depth
        group = self.group.partial_eval(Python).to_python(loop_depth)

        return PythonScript(
            merge_locals(frum.locals, group.locals, stream=stream, enlist=enlist),
            loop_depth,
            array_of(frum.type) | JxType(group=group.type),
            f"""[{group.source} for rows{loop_depth} in [enlist({frum.source})] for rownum{loop_depth}, row{loop_depth} in enumerate(rows{loop_depth})]""",
            self,
        )


def group(values, func):
    for g, rows in itertools.groupby(sorted(values, key=func), func):
        yield {_A: stream(rows), "group": g}
