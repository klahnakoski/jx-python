# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import exists

from jx_base.expressions import ToBooleanOp as _ToBooleanOp, FALSE, PythonScript
from jx_python.expressions._utils import with_var
from jx_python.utils import merge_locals
from mo_json import JX_BOOLEAN


class ToBooleanOp(_ToBooleanOp):
    def to_python(self, loop_depth=0):
        term = self.term.to_python(loop_depth)
        if term.jx_type == JX_BOOLEAN and term.miss is FALSE:
            return term
        return PythonScript(
            merge_locals(term.locals, exists=exists),
            loop_depth,
            JX_BOOLEAN,
            with_var("f", term.source, "exists(f) and f is not False"),
            self,
            FALSE,
        )
