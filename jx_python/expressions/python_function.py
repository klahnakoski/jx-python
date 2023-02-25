# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_math import randoms

from jx_base.expressions import Expression
from jx_base.expressions import PythonFunction as PythonFunction_
from jx_python.expressions._utils import PythonSource
from jx_python.utils import wrap_function


class PythonFunction(PythonFunction_):
    """
    Box a Python function, source unknown
    """

    def __init__(self, func):
        Expression.__init__(self, None)
        self.func = wrap_function(func)
        self._name = f"boxed_function{randoms.base64(8)}"

    def to_python(self):
        return PythonSource({self._name: self.func}, f"{self._name}(row, rownum, rows)")

    def __data__(self):
        return {"python_function": {}}

    def __str__(self):
        return "<python function>"
