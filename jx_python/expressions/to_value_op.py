# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions import ToValueOp as _ToValueOp, PythonScript
from jx_base.language import is_op
from jx_base.utils import delist
from jx_python.expressions import Python
from jx_python.utils import merge_locals


class ToValueOp(_ToValueOp):
    def to_python(self, loop_depth=0):
        term = self.term.partial_eval(Python).to_python(loop_depth)
        return PythonScript(
            merge_locals(term.locals, delist=delist), loop_depth, term.jx_type, f"delist({term.source})", self,
        )

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)
        if is_op(term, ToValueOp):
            return term
        return lang.ToValueOp(term)
