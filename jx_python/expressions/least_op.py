# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import LeastOp as _LeastOp
from jx_python.expressions.and_op import AndOp
from jx_python.expressions.python_script import PythonScript
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json import union_type


def least(decisive, values):
    best = None
    for v in values:
        if v is None:
            if decisive:
                continue  # skip nulls, take the smallest present value
            return None  # conservative: any null poisons the result
        if best is None or v < best:
            best = v
    return best


class LeastOp(_LeastOp):
    def to_python(self, loop_depth=0):
        terms = [t.partial_eval(Python).to_python(loop_depth) for t in self.terms]
        source, locals = zip(*((t.source, t.locals) for t in terms))
        return PythonScript(
            merge_locals(locals, least=least),
            loop_depth,
            union_type(*(t.jx_type for t in terms)),
            f"least({self.decisive}, [" + ",".join(source) + "])",
            self,
            AndOp(*(t.miss for t in terms)),
        )
