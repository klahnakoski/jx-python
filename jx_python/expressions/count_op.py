# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import CountOp as _CountOp
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions import Python
from mo_json import JX_INTEGER


class CountOp(_CountOp):
    def to_python(self, loop_depth=0):
        frum = self.frum.partial_eval(Python).to_python(loop_depth)
        loop_depth = frum.loop_depth + 1
        return PythonScript(
            frum.locals, loop_depth, JX_INTEGER, f"sum(((0 if v==None else 1) for v in {frum.source}), 0)", self
        )
