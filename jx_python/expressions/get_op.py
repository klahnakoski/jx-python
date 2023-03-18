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
from jx_base.expressions.python_script import PythonScript
from jx_python.utils import merge_locals
from mo_json import JX_ANY, ARRAY, array_of, is_many


class GetOp(GetOp_):
    def to_python(self, loop_depth=0):
        offsets, locals = zip(*((c.source, c.locals) for o in self.offsets for c in [o.to_python(loop_depth)]))
        offsets = ", ".join(offsets)
        var = self.var.to_python(loop_depth)
        if var.type == ARRAY:
            var_type = array_of(JX_ANY)
        else:
            var_type = JX_ANY

        return PythonScript(
            merge_locals(locals, var.locals, get_attr=get_attr),
            loop_depth,
            var_type,
            f"get_attr({var.source}, {offsets})",
            self,
        )


def unit(x):
    return x


def get_attr(value, *items):
    undo = delist
    if is_many(value):
        undo = unit

    values = enlist(value)
    for item in items:
        result = []
        for v in values:
            try:
                child = getattr(v, item)
            except:
                try:
                    child = v[item]
                except:
                    continue

            result.extend(enlist(child))

        values = result
    return undo(values)
