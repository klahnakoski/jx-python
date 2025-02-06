# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import TallyOp as _TallyOp
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_dots import is_missing
from mo_json import JX_INTEGER


class TallyOp(_TallyOp):
    def to_python(self, loop_depth=0):
        terms = [t.partial_eval(Python).to_python(loop_depth) for t in self.terms]

        return PythonScript(
            merge_locals(*(t.locals for t in terms), tally=tally),
            loop_depth,
            JX_INTEGER,
            f"tally({','.join(t.source for t in terms)})",
            self,
        )


def tally(*terms):
    output = 0
    for t in terms:
        if is_missing(t):
            return None
        output += 1
    return output
