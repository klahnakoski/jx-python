# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import TupleOp as TupleOp_


class TupleOp(TupleOp_):
    def to_python(self):
        if len(self.terms) == 0:
            return "tuple()"
        elif len(self.terms) == 1:
            return "(" + (self.terms[0]).to_python() + ",)"
        else:
            return "(" + ",".join((t).to_python() for t in self.terms) + ")"
