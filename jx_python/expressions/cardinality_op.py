# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import CardinalityOp as CardinalityOp_
from jx_python.expressions._utils import PythonSource


class CardinalityOp(CardinalityOp_):
    def to_python(self):
        if not self.terms:
            return PythonSource({}, "0")
        else:
            return PythonSource({}, "len(set(" + self.terms.to_python() + "))")
