# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import FilterOp as FilterOp_, Variable
from jx_base.utils import enlist
from jx_python.expressions import Python
from jx_base.expressions.python_script import PythonScript


class FilterOp(FilterOp_):
    def to_python(self, loop_depth):
        r = Variable("r")
        r.simplified = True
        rn = Variable("rn")
        rn.simplified = True
        rs = Variable("rs")
        rs.simplified = True

        predicate = (
            self
            .predicate
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
            {"enlist": enlist, **frum.locals, **predicate.locals},
            loop_depth,
            frum.type,
            f"[r for rs in [enlist({frum.source})] for rn, r in enumerate(rs) if"
            f" ({predicate.source})]",
            self,
        )
