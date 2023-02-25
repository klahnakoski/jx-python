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
    def to_python(self):
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
            .map({"row": r, "rownum": rn, "rows": rs})
            .to_python()
        )
        frum = self.frum.partial_eval(Python).to_python()

        return PythonScript(
            {}, f"[r for rs in [enlist({frum})] for rn, r in enumerate(rs) if ({func})]"
        )
