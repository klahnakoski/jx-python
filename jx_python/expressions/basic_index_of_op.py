# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import BasicIndexOfOp as _BasicIndexOfOp
from jx_python.expressions._utils import with_var, PythonScript
from jx_python.utils import merge_locals
from mo_json import JX_INTEGER


class BasicIndexOfOp(_BasicIndexOfOp):
    def to_python(self, loop_depth=0):
        find = self.find.to_python(loop_depth)
        value = self.value.to_python(loop_depth)

        return PythonScript(
            merge_locals(value.locals, find.locals),
            loop_depth,
            JX_INTEGER,
            f"({value.source}).find({find.source})",
            self,
        )
