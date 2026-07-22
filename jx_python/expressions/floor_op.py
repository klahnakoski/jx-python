# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import mo_math

from jx_base.expressions import FloorOp as _FloorOp
from jx_base.expressions.python_script import PythonScript
from jx_python.utils import merge_locals
from mo_json import JX_NUMBER


class FloorOp(_FloorOp):
    def to_python(self, loop_depth=0):
        lhs = self.lhs.to_python(loop_depth)
        rhs = self.rhs.to_python(loop_depth)
        return PythonScript(
            merge_locals(lhs.locals, rhs.locals, mo_math=mo_math),
            loop_depth,
            JX_NUMBER,
            f"mo_math.floor({lhs.source}, {rhs.source})",
            self,
        )
