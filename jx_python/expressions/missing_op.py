# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import MissingOp as MissingOp_, PythonScript, FALSE
from mo_json import JX_BOOLEAN


class MissingOp(MissingOp_):
    def to_python(self, loop_depth=0):
        expr = self.expr.to_python(loop_depth)
        return PythonScript(expr.locals, loop_depth, JX_BOOLEAN, expr.source + " == None", self, FALSE)
