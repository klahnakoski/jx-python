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
        acc = [f"for v0 in listwrap({self.var.to_python()})"]
        for i, o in enumerate(self.offsets):
            getting = f"get_attr(v{i}, {o.to_python()})"
            acc.append(f"for v{i+1} in {getting}")
        n = len(self.offsets)
        return destream(f"[v{n} " + " ".join(acc) + "]")


def destream(code):
    return f"[None if len(c)==0 else c[0] if len(c)==1 else c for c in [{code}]][0]"
