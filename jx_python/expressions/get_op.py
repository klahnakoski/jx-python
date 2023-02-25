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
from jx_base.utils import enlist, delist
from jx_python.expressions._utils import PythonSource


class GetOp(GetOp_):
    def to_python(self):
        offsets, locals = zip(*((c.source, c.locals) for o in self.offsets for c in [o.to_python()]))
        offsets = ", ".join(offsets)
        locals = locals+ ({"get_attr": get_attr},)
        return PythonSource({k: v for l in locals for k, v in l.items()}, f"get_attr({self.var.to_python()}, {offsets})")


def get_attr(value, *items):
    values = enlist(value)
    for item in items:
        result = []
        for v in values:
            try:
                result.extend(enlist(getattr(v, item)))
                continue
            except:
                pass

            try:
                result.extend(enlist(v[item]))
            except:
                pass

        values = result
    return delist(values)



