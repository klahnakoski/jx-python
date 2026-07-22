# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import StrictIndexOfOp as _StrictIndexOfOp
from jx_python.expressions._utils import with_var, PythonScript
from jx_python.utils import merge_locals
from mo_json import JX_INTEGER


class StrictIndexOfOp(_StrictIndexOfOp):
    def to_python(self, loop_depth=0):
        find = self.find.to_python(loop_depth)
        value = self.value.to_python(loop_depth)

        # the dynamically typed target may hold a non-string here; .find only
        # exists on strings, so anything else is "not found" (-1)
        source = with_var(
            "v",
            value.source,
            with_var(
                "g",
                find.source,
                "(v.find(g) if isinstance(v, str) and isinstance(g, str) else -1)",
            ),
        )
        return PythonScript(
            merge_locals(value.locals, find.locals),
            loop_depth,
            JX_INTEGER,
            source,
            self,
        )
