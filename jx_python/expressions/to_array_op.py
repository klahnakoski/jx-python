# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import ToArrayOp as _ToArrayOp, PythonScript
from jx_base.utils import enlist
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json import array_of


class ToArrayOp(_ToArrayOp):
    def to_python(self, loop_depth=0):
        term = self.term.partial_eval(Python).to_python(loop_depth)
        return PythonScript(
            merge_locals(term.locals, enlist=enlist),
            loop_depth,
            array_of(term.jx_type),
            f"enlist({term.source})",
            self,
        )
