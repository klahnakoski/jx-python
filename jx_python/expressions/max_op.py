# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import MaxOp as _MaxOp
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions import Python


class MaxOp(_MaxOp):
    def to_python(self, loop_depth=0):
        frum = self.frum.partial_eval(Python).to_python(loop_depth+1)
        source, locals = frum.source, frum.locals
        return PythonScript(
            locals,
            loop_depth,
            frum.jx_type,
            f"max({source})",
            self
        )
