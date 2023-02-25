# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import ConcatOp as ConcatOp_
from jx_base.expressions.python_script import PythonScript


class ConcatOp(ConcatOp_):
    def to_python(self):
        v = (self.value).to_python()
        l = (self.length).to_python()
        return PythonScript(
            {},
            (
                "None if "
                + v
                + " == None or "
                + l
                + " == None else "
                + v
                + "[0:max(0, "
                + l
                + ")]"
            ),
        )
