# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import PercentileOp as _PercentileOp
from jx_python.expressions._utils import multiop_to_python


class PercentileOp(_PercentileOp):
    to_python = multiop_to_python
