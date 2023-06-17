# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import FirstOp as FirstOp_
from jx_base.expressions.python_script import PythonScript
from jx_base.utils import enlist
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_future import first
from mo_json import member_type, ARRAY_KEY


class FirstOp(FirstOp_):
    def to_python(self, loop_depth=0):
        value = self.term.partial_eval(Python).to_python(loop_depth)
        return PythonScript(
            merge_locals(value.locals, first=first, enlist=enlist, ARRAY_KEY=ARRAY_KEY),
            loop_depth,
            member_type(value.type),
            f"first(enlist({value.source}))",
            self,
        )
