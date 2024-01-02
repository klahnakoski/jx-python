# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.base_multi_op import BaseMultiOp
from jx_base.expressions.literal import Literal, is_literal
from jx_base.expressions.null_op import NULL
from mo_math import MAX


class MostOp(BaseMultiOp):
    """
    CONSERVATIVE MAXIMUM (SEE MaxOp FOR DECISIVE MAXIMUM)
    """
    pass
