# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import AndOp as AndOp_, FALSE
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions.to_boolean_op import ToBooleanOp
from mo_json import JX_BOOLEAN


class AndOp(AndOp_):
    def to_python(self):
        if not self.terms:
            return PythonScript({}, JX_BOOLEAN, "True", self, FALSE)
        else:
            sources, locals = zip(*((c.source, c.locals) for t in self.terms for c in [ToBooleanOp(t).to_python()]))
            return PythonScript(
                {k:v for l in locals for k, v in l.items()}, JX_BOOLEAN, " and ".join(sources), self, FALSE
            )
