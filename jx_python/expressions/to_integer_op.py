# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import ToIntegerOp as _IntegerOp
from jx_base.expressions.python_script import PythonScript
from mo_json import JX_INTEGER


class ToIntegerOp(_IntegerOp):
    def to_python(self, loop_depth=0):
        return PythonScript({}, loop_depth, JX_INTEGER, "int(" + self.term.to_python(loop_depth) + ")", self)
