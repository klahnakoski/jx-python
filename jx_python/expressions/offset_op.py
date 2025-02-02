# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import OffsetOp as _OffsetOp
from jx_base.expressions.python_script import PythonScript


class OffsetOp(_OffsetOp):
    def to_python(self, loop_depth=0):
        return PythonScript({}, loop_depth, f"row[{self.var}] if 0<={self.var}<len(row) else None",)
