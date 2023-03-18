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

from jx_base.expressions import Variable as Variable_
from jx_base.expressions.python_script import PythonScript
from mo_json import JX_ANY


class Variable(Variable_):
    def to_python(self, loop_depth):
        if self.var not in ["row", "rownum", "rows"]:
            logger.error("not expected")
        return PythonScript({}, loop_depth, JX_ANY, f"{self.var}{loop_depth}", self)
