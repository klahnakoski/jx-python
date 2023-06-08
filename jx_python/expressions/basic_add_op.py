# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import BasicAddOp as BasicAddOp_, FALSE
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json import JX_BOOLEAN


class BasicAddOp(BasicAddOp_):
    def to_python(self, loop_depth=0):
        terms = [t.partial_eval(Python).to_python(loop_depth) for t in self.terms]
        return PythonScript(
            merge_locals(*(t.locals for t in terms)),
            loop_depth,
            JX_BOOLEAN,
            " + ".join(f"({t.source})" for t in terms),
            FALSE,
        )
