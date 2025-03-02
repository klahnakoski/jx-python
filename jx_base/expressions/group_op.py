# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions.expression import Expression, MissingOp
from mo_json import array_of


class GroupOp(Expression):
    """
    return a series of {"group": group, "part": list_of_rows_for_group}
    """

    def __init__(self, frum, group):
        Expression.__init__(self, frum, group)
        self.frum, self.group = frum, group

    def __data__(self):
        return {"group": [self.frum.__data__(), self.group.__data__()]}

    def vars(self):
        return self.frum.vars() | self.group.vars()

    def map(self, map_):
        return GroupOp(self.frum.map(map_), self.group.map(map_))

    @property
    def jx_type(self):
        return array_of(self.frum.jx_type)

    def missing(self, lang):
        return MissingOp(self)

    def invert(self, lang):
        return self.missing(lang)


def _normalize_groupby(groupby, limit, schema=None):
    if groupby == None:
        return None
    output = list_to_data([n for e in enlist(groupby) for n in _normalize_group(e, None, limit, schema=schema)])
    for i, o in enumerate(output):
        o.dim = i
    if any(o == None for o in output):
        Log.error("not expected")
    return output


def _normalize_group(edge, dim_index, limit, schema=None):
    """
    :param edge: Not normalized groupby
    :param dim_index: Dimensions are ordered; this is this groupby's index into that order
    :param schema: for context
    :return: a normalized groupby
    """
    if is_text(edge):
        if edge == "*":
            return list_to_data([{
                "name": ".",
                "value": LeavesOp(Variable(".")),
                "allowNulls": True,
                "dim": dim_index,
                "domain": DefaultDomain(limit=limit, desc=edge),
            }])
        elif edge.endswith(".*"):
            prefix = edge[:-2]
            return list_to_data([{
                "name": ".",
                "value": LeavesOp(Variable(prefix)),
                "allowNulls": True,
                "dim": dim_index,
                "domain": DefaultDomain(limit=limit, desc=edge),
            }])
        return list_to_data([{
            "name": edge,
            "value": jx_expression(edge),
            "allowNulls": True,
            "dim": dim_index,
            "domain": DefaultDomain(limit=limit, desc=edge),
        }])
    else:
        edge = to_data(edge)
        if edge.domain and edge.domain.jx_type != "default":
            Log.error("groupby does not accept complicated domains")

        if not edge.name and not is_text(edge.value):
            Log.error("You must name compound edges: {edge}", edge=edge)

        return list_to_data([{
            "name": coalesce(edge.name, edge.value),
            "value": jx_expression(edge.value),
            "allowNulls": True,
            "dim": dim_index,
            "domain": DefaultDomain(limit=limit, desc=edge),
        }])


