# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_logs import logger

from jx_base.expressions.to_array_op import ToArrayOp
from jx_base.expressions.expression import Expression
from jx_base.language import is_op
from jx_python.utils import _array_source_prefix
from mo_imports import export
from mo_json.types import JX_BOOLEAN


class PythonToListOp(Expression):
    _data_type = JX_BOOLEAN

    def __init__(self, array):
        Expression.__init__(self, array)
        self.array = array

    def __data__(self):
        return {"python.to_list": self.array.__data__()}

    def __call__(self, row, rownum=None, rows=None):
        return to_python_list(self.array(row, rownum, rows))

    def __eq__(self, other):
        if not is_op(other, PythonToListOp):
            return False
        return self.array == other.array

    def vars(self):
        return self.array.vars()

    def map(self, map_):
        return PythonToListOp(self.array.map(map_))

    def missing(self, lang):
        return self.array.missing(lang)

    def invert(self, lang):
        return self.missing(lang)


def to_python_list(expression):
    """
    jx puts all arrays in typed json, like {"~a~": [content, of, list]}
    return the python array
    """

    if expression.startswith(_array_source_prefix) and expression.endswith("}"):
        return expression[len(_array_source_prefix) : -1].strip()
    else:
        return f"({expression})[ARRAY_KEY]"


export("jx_base.expressions.to_array_op", PythonToListOp)
