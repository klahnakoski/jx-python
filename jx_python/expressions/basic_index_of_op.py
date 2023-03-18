# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import BasicIndexOfOp as BasicIndexOfOp_
from jx_python.expressions._utils import with_var, PythonScript


class BasicIndexOfOp(BasicIndexOfOp_):
    def to_python(self, loop_depth):
        return PythonScript(
            {},
            loop_depth,
            with_var(
                "f",
                "("
                + (self.value).to_python(loop_depth)
                + ").find"
                + "("
                + (self.find).to_python(loop_depth)
                + ")",
                "None if f==-1 else f",
            ),
        )
