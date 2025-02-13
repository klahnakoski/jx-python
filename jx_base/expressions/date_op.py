# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.literal import Literal
from mo_dots import coalesce, is_data
from mo_imports import export
from mo_json.types import JX_TIME
from mo_times.dates import Date


class DateOp(Literal):
    date_type = JX_TIME

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, term):
        if is_data(term):
            term = term["date"]  # FOR WHEN WE MIGHT DO Literal({"date":term})
        self.date = term
        Literal.__init__(self, float(Date(self.date)))

    @classmethod
    def define(cls, expr):
        term = expr.get("date")
        if is_data(term):
            term = coalesce(term.get("literal"), term)
        return DateOp(term)

    def __data__(self):
        return {"date": self.date}

    def __call__(self, row=None, rownum=None, rows=None):
        return Date(self.date)

    @property
    def jx_type(self):
        return self.date_type


export("jx_base.expressions.literal", DateOp)
