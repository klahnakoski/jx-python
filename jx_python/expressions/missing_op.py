# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import is_missing
from mo_json.typed_object import TypedObject

from jx_base.expressions import MissingOp as _MissingOp, FALSE
from jx_python.expressions.python_script import PythonScript
from jx_python.utils import merge_locals
from mo_json import JX_BOOLEAN


class MissingOp(_MissingOp):
    def to_python(self, loop_depth=0):
        expr = self.expr.to_python(loop_depth)
        return PythonScript(
            merge_locals(expr.locals, missing=missing, is_missing=is_missing),
            loop_depth,
            JX_BOOLEAN,
            f"is_missing({expr.source})",
            self,
            FALSE,
        )


def missing(value):
    if isinstance(value, TypedObject):
        return is_missing(value._boxed_value)
    return is_missing(value)