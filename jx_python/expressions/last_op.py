# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import LastOp as LastOp_
from jx_python.expressions._utils import PythonSource


class LastOp(LastOp_):
    def to_python(self):
        term = self.term.to_python()
        return PythonSource({}, "last(" + term + ")")
