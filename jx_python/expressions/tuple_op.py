# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base import FALSE
from jx_python.utils import merge_locals

from jx_base.expressions import TupleOp as _TupleOp
from jx_base.expressions.python_script import PythonScript


class TupleOp(_TupleOp):
    def to_python(self, loop_depth=0):
        sources, locals, jx_type = zip(
            *((c.source, c.locals, c.jx_type) for t in self.terms for c in [t.to_python(loop_depth)])
        )
        if len(self.terms) == 0:
            prefix, suffix = "tuple(", ")"
        elif len(self.terms) == 1:
            prefix, suffix = "(", ",)"
        else:
            prefix, suffix = "(", ")"

        return PythonScript(
            locals=merge_locals(*locals),
            loop_depth=loop_depth,
            type={str(i) for i, t in enumerate(jx_type)},
            source=f"{prefix}{', '.join(sources)}{suffix}",
            frum=self,
            miss=FALSE,
            many=FALSE,
        )
