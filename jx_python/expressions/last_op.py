# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import is_many

from jx_base.expressions import LastOp as LastOp_
from jx_base.expressions.python_script import PythonScript
from jx_python.utils import merge_locals
from mo_json import member_type


class LastOp(LastOp_):
    def to_python(self, loop_depth=0):
        term = self.term.to_python(loop_depth)
        return PythonScript(
            merge_locals(term.locals, last=last), loop_depth, member_type(term.type), f"last({term.source})", self,
        )


def last(values):
    if isinstance(values, (tuple, list)):
        return values[-1]
    if is_many(values):
        last = None
        for v in values:
            last = v
        return last
    return values
