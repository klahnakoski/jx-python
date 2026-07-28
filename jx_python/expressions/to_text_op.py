# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions.python_script import PythonScript

from jx_base.expressions import ToTextOp as _ToTextOp
from jx_python.expressions._utils import Python
from jx_python.utils import merge_locals
from mo_json import JX_TEXT


def to_text(v):
    if isinstance(v, float) and v.is_integer():
        return str(int(v))  # 2.0 -> "2", not "2.0"
    return str(v)


class ToTextOp(_ToTextOp):
    def to_python(self, loop_depth=0):
        missing = self.term.missing(Python).to_python(loop_depth)
        value = self.term.to_python(loop_depth)
        return PythonScript(
            locals=merge_locals(value.locals, to_text=to_text),
            loop_depth=loop_depth,
            type=JX_TEXT,
            source=f"to_text({value.source})",  # coerce to text (missing handled by miss)
            frum=self,
            miss=missing,
        )
