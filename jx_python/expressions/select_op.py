# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import leaves_to_data
from mo_logs.strings import quote

from jx_base.expressions import SelectOp as SelectOp_
from jx_base.expressions.python_script import PythonScript
from jx_base.expressions.select_op import SelectOne
from jx_base.utils import enlist, delist
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json import array_of


class SelectOp(SelectOp_):
    def to_python(self, loop_depth=0):
        frum = self.frum.partial_eval(Python).to_python(loop_depth)
        loop_depth = frum.loop_depth + 1
        selects = tuple(
            SelectOne(t.name, t.value.partial_eval(Python).to_python(loop_depth),)
            for t in self.terms
        )

        if len(selects) == 1 and selects[0].name == ".":
            # value selection
            source = f"""delist([{selects[0].value.source} for rows{loop_depth} in [enlist({frum.source})] for rownum{loop_depth}, row{loop_depth} in enumerate(rows{loop_depth})])"""
        else:
            # structure selection
            select_sources = ",".join(
                quote(s.name) + ":" + s.value.source for s in selects
            )
            source = f"""delist([leaves_to_data({{{select_sources}}}) for rows{loop_depth} in [enlist({frum.source})] for rownum{loop_depth}, row{loop_depth} in enumerate(rows{loop_depth})])"""

        return PythonScript(
            merge_locals(
                [s.value.locals for s in selects],
                frum.locals,
                leaves_to_data=leaves_to_data,
                enlist=enlist,
                delist=delist,
            ),
            loop_depth,
            array_of(self.type),
            source,
            self,
        )
