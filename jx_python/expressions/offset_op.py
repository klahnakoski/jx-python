# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from mo_future import text

from jx_base.expressions import OffsetOp as OffsetOp_
from jx_base.expressions.python_script import PythonScript


class OffsetOp(OffsetOp_):
    def to_python(self, loop_depth):
        return PythonScript(
            {},
            loop_depth,
            (
                "row["
                + text(self.var)
                + "] if 0<="
                + text(self.var)
                + "<len(row) else None"
            ),
        )
