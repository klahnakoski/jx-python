# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import FalseOp as FalseOp_
from jx_base.expressions.python_script import PythonScript


class FalseOp(FalseOp_):
    def to_python(self, loop_depth):
        return PythonScript({}, loop_depth, "False")
