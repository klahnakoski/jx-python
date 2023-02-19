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
from jx_base.language import value_compare


class EqOp(EqOp_):
    def to_python(self):
        return (
            "("
            + self.rhs.to_python()
            + ") in enlist("
            + self.lhs.to_python()
            + ")"
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
