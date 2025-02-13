# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import LengthOp as _LengthOp
from jx_base.expressions.python_script import PythonScript
from mo_json import JX_INTEGER


class LengthOp(_LengthOp):
    def to_python(self, loop_depth=0):
        value = self.term.to_python(loop_depth)
        return PythonScript(
            value.locals, loop_depth, JX_INTEGER, f"len({value.source}) if ({value.source}) != None else None", self
        )
