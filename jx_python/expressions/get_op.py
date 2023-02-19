# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import GetOp as GetOp_


class GetOp(GetOp_):
    def to_python(self):
        offsets = ", ".join(o.to_python() for o in self.offsets)
        return f"get_attr({self.var.to_python()}, {offsets})"
