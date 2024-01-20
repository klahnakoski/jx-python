# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import IsTextOp as _IsTextOp, PythonScript
from jx_base.expressions.to_boolean_op import ToBooleanOp
from mo_json.types import JX_TEXT


class IsTextOp(_IsTextOp):
    def to_python(self, loop_depth=0):
        term = self.term.to_python(loop_depth)
        return PythonScript(
            term.locals,
            loop_depth,
            JX_TEXT,
            f"[v if isinstance(v, str) else None for v in [{term.source}]][0]",
            self,
            ToBooleanOp(self)
        )

