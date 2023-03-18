# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import FilterOp as FilterOp_
from jx_base.expressions.python_script import PythonScript
from jx_base.utils import enlist
from jx_python.expressions import Python


class FilterOp(FilterOp_):
    def to_python(self, loop_depth=0):
        frum = self.frum.partial_eval(Python).to_python(loop_depth)
        loop_depth = frum.loop_depth + 1
        predicate = self.predicate.partial_eval(Python).to_python(loop_depth)

        return PythonScript(
            {"enlist": enlist, **frum.locals, **predicate.locals},
            loop_depth,
            frum.type,
            f"""[row{loop_depth} for rows{loop_depth} in [enlist({frum.source})] for rownum{loop_depth}, row{loop_depth} in enumerate(rows{loop_depth}) if ({predicate.source})]""",
            self,
        )
