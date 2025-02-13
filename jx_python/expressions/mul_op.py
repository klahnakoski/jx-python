# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import MulOp as _MulOp
from jx_python.expressions._utils import multiop_to_python


class MulOp(_MulOp):
    """
    CONSERVATIVE MULTIPLICATION (SEE ProductOp FOR DECISIVE MULTIPLICATION)
    """

    to_python = multiop_to_python
