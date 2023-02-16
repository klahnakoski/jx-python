# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import CaseOp as CaseOp_


class CaseOp(CaseOp_):
    def to_python(self):
        acc = (self.whens[-1]).to_python()
        for w in reversed(self.whens[0:-1]):
            acc = (
                "("
                + w.then.to_python()
                + ") if ("
                + w.when.to_python()
                + ") else ("
                + acc
                + ")"
            )
        return acc
