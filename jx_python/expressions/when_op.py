# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_imports import export

from jx_base.expressions import WhenOp as WhenOp_


class WhenOp(WhenOp_):
    def to_python(self):
        return (
            "("
            + self.then.to_python()
            + ") if ("
            + self.when.to_python()
            + ") else ("
            + self.els_.to_python()
            + ")"
        )


export("jx_python.expressions._utils", WhenOp)
