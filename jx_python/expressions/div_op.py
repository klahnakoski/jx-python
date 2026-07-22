# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import DivOp as _DivOp, EqOp, OrOp
from jx_base.expressions.literal import ZERO
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions._utils import Python, with_var
from jx_python.utils import merge_locals
from mo_json import JX_NUMBER


class DivOp(_DivOp):
    def to_python(self, loop_depth=0):
        lhs = self.lhs.to_python(loop_depth)
        rhs = self.rhs.to_python(loop_depth)
        # decisive: a non-numeric/null dividend, or a null/zero divisor, yields
        # null (no ZeroDivisionError) -- mirrors DivOp.__call__
        source = with_var(
            "d",
            rhs.source,
            with_var(
                "n",
                lhs.source,
                "(n / d) if (isinstance(n, (int, float)) and isinstance(d, (int, float)) and d) else None",
            ),
        )
        missing = OrOp(
            self.lhs.missing(Python), self.rhs.missing(Python), EqOp(self.rhs, ZERO)
        ).partial_eval(Python)
        return PythonScript(merge_locals(lhs.locals, rhs.locals), loop_depth, JX_NUMBER, source, self, missing)
