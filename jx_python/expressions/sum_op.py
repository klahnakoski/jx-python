# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_json.typed_object import TypedObject, entype

from jx_python.expressions._utils import with_var
from mo_dots import exists

from jx_base.expressions import SumOp as _SumOp, PythonScript, ToArrayOp
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json import JX_NUMBER


class SumOp(_SumOp):
    def to_python(self, loop_depth=0):
        term = ToArrayOp(self.frum).partial_eval(Python).to_python(loop_depth)
        loop_depth = term.loop_depth + 1
        term_code = f"source{loop_depth}"
        source = f"""TypedObject(sum(row{loop_depth} for row{loop_depth} in {term_code} if exists(row{loop_depth})), **{term_code}._attachments)"""
        source = with_var(term_code, f"entype({term.source})", source)
        return PythonScript(
            merge_locals(term.locals, TypedObject=TypedObject, exists=exists, entype=entype),
            loop_depth,
            JX_NUMBER,
            source,
            self,
        )
