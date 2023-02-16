# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import FloorOp as FloorOp_


class FloorOp(FloorOp_):
    def to_python(self):
        return (
            "mo_math.floor("
            + (self.lhs).to_python()
            + ", "
            + (self.rhs).to_python()
            + ")"
        )
