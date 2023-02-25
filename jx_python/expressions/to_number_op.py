# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_imports import export

from jx_base.expressions.python_script import PythonScript
from mo_json.types import JX_NUMBER_TYPES, JX_NUMBER

from jx_base.expressions.to_number_op import ToNumberOp as NumberOp_
from jx_base.expressions.true_op import TRUE


class ToNumberOp(NumberOp_):
    def to_python(self):
        term = self.term
        exists = self.term.exists()
        value = self.term.to_python()

        if exists is TRUE:
            if term.type in JX_NUMBER_TYPES:
                return value
            return PythonScript({**value.locals}, JX_NUMBER, "float(" + value.source + ")")
        else:
            return PythonScript(
                {**value.locals},
                JX_NUMBER,
                "float(" + value + ") if (" + exists.to_python().source + ")",
            )


export("jx_python.expressions._utils", ToNumberOp)
