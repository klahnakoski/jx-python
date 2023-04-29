# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import PythonToListOp as PythonToListOp_, PythonScript, ToArrayOp
from jx_base.expressions.python_to_list_op import to_python_list
from mo_json import JX_ANY


class PythonToListOp(PythonToListOp_):
    def to_python(self, loop_depth=0):
        array = ToArrayOp(self.array.to_python(loop_depth))
        return PythonScript(array.locals, loop_depth, JX_ANY, to_python_list(array.source), self)
