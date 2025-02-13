# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import RightOp as _RightOp
from jx_python.expressions._utils import with_var, PythonScript


class RightOp(_RightOp):
    def to_python(self, loop_depth=0):
        v = (self.value).to_python(loop_depth)
        l = (self.length).to_python(loop_depth)

        return PythonScript(
            {}, loop_depth, with_var("v", v, "None if v == None else v[max(0, len(v)-int(" + l + ")):]"),
        )
