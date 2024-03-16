# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import LastOp as _LastOp, ToArrayOp
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json import member_type, ARRAY_KEY
from mo_json.typed_object import TypedObject


class LastOp(_LastOp):
    def to_python(self, loop_depth=0):
        term = ToArrayOp(self.term).partial_eval(Python).to_python(loop_depth)
        return PythonScript(
            merge_locals(term.locals, last=last), loop_depth, member_type(term.jx_type), f"last({term.source})", self,
        )


def last(values):
    if isinstance(values, TypedObject):
        if values[ARRAY_KEY] is not None:
            return values[ARRAY_KEY][-1]
        else:
            return values
    if not values:
        return None
    return values[-1]
