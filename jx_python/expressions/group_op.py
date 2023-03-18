# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import GroupOp as GroupOp_, Variable
from jx_python.expressions import Python
from jx_base.expressions.python_script import PythonScript


class GroupOp(GroupOp_):
    def to_python(self, loop_depth):
        r = Variable("r")
        r.simplified = True
        rn = Variable("rn")
        rn.simplified = True
        rs = Variable("rs")
        rs.simplified = True

        func = (
            self
            .select
            .partial_eval(Python)
            .map(dict(
                row=f"row{loop_depth}",
                rownum=f"rownum{loop_depth}",
                rows=f"rows{loop_depth}",
            ))
            .to_python(loop_depth)
        )
        frum = self.frum.partial_eval(Python).to_python(loop_depth)

        return PythonScript(
            {},
            loop_depth,
            f"[r for rs in [enlist({frum})] for rn, r in enumerate(rs) if ({func})]",
        )
