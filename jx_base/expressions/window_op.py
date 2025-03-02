# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import jx_expression, Expression
from mo_imports import expect

jx = expect("jx")


class OneWindow:

    def __init__(
        self,
        *,
        select=None,
        edges=None,
        where=None,
        sort=None,
        range=None
    ):
        self.select = select
        self.edges = edges
        self.where = where
        self.sort = sort
        self.range = range


class WindowOp(Expression):
    def __init__(self, frum, window):
        Expression.__init__(self, frum)
        if not isinstance(window, OneWindow):
            raise Exception("window must be a OneWindow structure")
        self.frum = frum
        self.window = window

    @classmethod
    def define(cls, expr):
        raw_frum, *raw_windows = expr["window"]
        frum = jx_expression(raw_frum, cls.lang)
        for raw_window in raw_windows:
            new_window = {}
            for slot, attr in [("edges", "edges"), ("where", "predicate"), ("filter", "predicate"), ("sort", "sorts")]:
                if raw_window[slot]:
                    temp = jx_expression({"from": frum, slot: raw_window[slot]})
                    new_window[slot] = getattr(temp, attr)
            temp = jx_expression({
                "from": frum,
                "select": {k: raw_window[k] for k in ["name", "value", "aggregate"]}
            })
            new_window["select"] = temp.terms
            new_window["range"] = raw_window["range"]
            frum = WindowOp(frum, OneWindow(**new_window))
        return frum

    def __call__(self, row=None, rownum=None, rows=None):
        data = self.frum(row, rownum, rows)
        return jx.window(data, window=self.window)
