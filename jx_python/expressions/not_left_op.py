# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import NotLeftOp as NotLeftOp_
from jx_python.expressions._utils import PythonSource


class NotLeftOp(NotLeftOp_):
    def to_python(self):
        v = self.value.to_python()
        l = self.length.to_python()
        return PythonSource(
            {**v.locals, **l.locals},
            (
                "None if "
                + v
                + " == None or "
                + l.source
                + " == None else "
                + v.source
                + "[max(0, "
                + l.source
                + "):]"
            ),
        )
