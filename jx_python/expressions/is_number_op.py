# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import IsNumberOp as _IsNumberOp, PythonScript
from jx_python.expressions._utils import Python
from mo_json.types import JX_NUMBER


class IsNumberOp(_IsNumberOp):
    def to_python(self, loop_depth=0):
        term = self.term.to_python(loop_depth)
        return PythonScript(
            term.locals,
            loop_depth,
            JX_NUMBER,
            f"[v if isinstance(v, (int, float)) and not isinstance(v, bool) else None for v in [{term.source}]][0]",
            self,
            self.term.missing(Python),
        )
