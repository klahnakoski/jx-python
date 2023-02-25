# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import EqOp as EqOp_, is_literal, FALSE, TRUE
from jx_base.expressions.python_script import PythonScript
from jx_base.language import value_compare
from jx_base.utils import enlist
from mo_json import JX_BOOLEAN


class EqOp(EqOp_):
    def to_python(self):
        lhs = self.lhs.to_python()
        rhs = self.rhs.to_python()
        return PythonScript(
            {"enlist": enlist, **rhs.locals, **lhs.locals},
            JX_BOOLEAN,
            f"({rhs.source}) in enlist({lhs.source})",
            self,
            FALSE
        )

    def partial_eval(self, lang):
        lhs = self.lhs.partial_eval(lang)
        rhs = self.rhs.partial_eval(lang)

        if lhs is self.lhs and rhs is self.rhs:
            return self
        if is_literal(lhs) and is_literal(rhs):
            return FALSE if value_compare(lhs.value, rhs.value) else TRUE
        else:
            return EqOp(lhs, rhs)
