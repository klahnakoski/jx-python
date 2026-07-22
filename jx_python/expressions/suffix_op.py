# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import SuffixOp as _SuffixOp
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions._utils import with_var
from jx_python.utils import merge_locals
from mo_json import JX_BOOLEAN


class SuffixOp(_SuffixOp):
    def to_python(self, loop_depth=0):
        expr = self.expr.to_python(loop_depth)
        suffix = self.suffix.to_python(loop_depth)
        return PythonScript(
            merge_locals(expr.locals, suffix.locals),
            loop_depth,
            JX_BOOLEAN,
            with_var(
                "e",
                expr.source,
                with_var("s", suffix.source, "False if e is None or s is None else e.endswith(s)"),
            ),
            self,
        )
