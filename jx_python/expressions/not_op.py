# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import NotOp as NotOp_
from jx_python.expressions._utils import PythonSource
from jx_python.expressions.to_boolean_op import ToBooleanOp


class NotOp(NotOp_):
    def to_python(self):
        term = ToBooleanOp(self.term).to_python()
        return PythonSource(term.locals, "not (" + term.source + ")")
