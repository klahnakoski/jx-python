# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions.python_script import PythonScript

from jx_base.expressions import ToTextOp as ToTextOp_
from jx_python.expressions._utils import Python


class ToTextOp(ToTextOp_):
    def to_python(self):
        missing = self.term.missing(Python)
        value = self.term.to_python()
        return PythonScript(
            value.locals,
            value.type,
            value.source,
            self,
            missing
        )
