# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import ArrayOfOp as _ToArrayOp, PythonScript
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json import array_of, ARRAY


class ArrayOfOp(_ToArrayOp):
    def to_python(self, loop_depth=0):
        term = self.term.partial_eval(Python).to_python(loop_depth)
        type = term.jx_type
        if type == ARRAY:
            return PythonScript(merge_locals(term.locals), loop_depth, type, term.source, self)

        return PythonScript(term.locals, loop_depth, array_of(term.jx_type), f"[{term.source}]", self,)
