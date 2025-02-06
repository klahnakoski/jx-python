# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import FindOp as _FindOp
from jx_python.expressions._utils import with_var, Python, PythonScript
from jx_python.expressions.literal import Literal
from jx_python.utils import merge_locals
from mo_json import JX_INTEGER


class FindOp(_FindOp):
    def partial_eval(self, lang):
        index = lang.StrictIndexOfOp(self.value, self.find, self.start).partial_eval(lang)

        output = (
            lang
            .WhenOp(
                lang.OrOp(self.value.missing(Python), self.find.missing(Python), lang.StrictEqOp(index, Literal(-1))),
                **{"else": index},
            )
            .partial_eval(lang)
        )
        return output

    def missing(self, lang):
        output = (
            lang
            .OrOp(
                self.value.missing(Python),
                self.find.missing(Python),
                lang.EqOp(lang.StrictIndexOfOp(self.value, self.find, self.start), Literal(-1)),
            )
            .partial_eval(lang)
        )
        return output

    def to_python(self, loop_depth=0):
        value = self.value.to_python(loop_depth)
        find = self.find.to_python(loop_depth)
        return PythonScript(
            merge_locals(value.locals, find.locals),
            loop_depth,
            JX_INTEGER,
            with_var("f", f"({value.source}).find({find.source})", "None if f==-1 else f",),
            self,
        )
