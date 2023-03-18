# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.basic_starts_with_op import (
    BasicStartsWithOp as _BasicStartsWithOp,
)
from jx_base.expressions.python_script import PythonScript


class BasicStartsWithOp(_BasicStartsWithOp):
    def to_python(self, loop_depth):
        return PythonScript(
            {},
            loop_depth,
            f"({self.value.to_python(loop_depth)}).startswith({self.prefix.to_python(loop_depth)})",
        )
