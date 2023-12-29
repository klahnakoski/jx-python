# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import coalesce
from mo_json import union_type

from jx_base import Python
from jx_base.expressions import CoalesceOp as _CoalesceOp
from jx_base.expressions.python_script import PythonScript
from jx_python.utils import merge_locals


class CoalesceOp(_CoalesceOp):
    def to_python(self, loop_depth=0):
        terms = [t.partial_eval(Python).to_python(loop_depth) for t in self.terms]
        return PythonScript(
            merge_locals(*(t.locals for t in terms), {"coalesce": coalesce}),
            loop_depth,
            union_type(*(t.jx_type for t in terms)),
            "coalesce(" + ", ".join(t.source for t in terms) + ")",
            self,
        )
