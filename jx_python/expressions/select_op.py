# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import leaves_to_data

from jx_base.expressions import SelectOp as _SelectOp, ToArrayOp
from jx_base.expressions.python_script import PythonScript
from jx_base.expressions.select_op import SelectOne
from jx_base.expressions.variable import is_variable
from jx_base.utils import delist
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json import array_of, ARRAY_KEY
from mo_logs.strings import quote


class SelectOp(_SelectOp):
    def to_python(self, loop_depth=0):
        frum = ToArrayOp(self.frum).partial_eval(Python).to_python(loop_depth)
        loop_depth = frum.loop_depth + 1
        selects = tuple(SelectOne(t.name, t.expr.partial_eval(Python).to_python(loop_depth)) for t in self.terms)

        if len(self.terms) == 1 and self.terms[0].name == ".":
            # value selection
            if is_variable(self.terms[0].expr) and self.terms[0].expr.var == "row":
                # SELECT ".", NO NEED TO LOOP
                loop_depth = frum.loop_depth
                source = frum.source
            else:
                # select property
                source = f"""[{selects[0].value.source} for row{loop_depth} in {frum.source}]"""
        else:
            # structure selection
            select_sources = ",".join(quote(s.name) + f": {s.value.source}" for s in selects)
            source = f"""[leaves_to_data({{{select_sources}}}) for row{loop_depth} in {frum.source}]"""

        return PythonScript(
            merge_locals(
                [s.value.locals for s in selects],
                frum.locals,
                leaves_to_data=leaves_to_data,
                delist=delist,
                ARRAY_KEY=ARRAY_KEY,
            ),
            loop_depth,
            array_of(self.jx_type),
            source,
            self,
        )
