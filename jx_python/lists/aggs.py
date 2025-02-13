# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import itertools

from jx_base.domains import DefaultDomain, SimpleSetDomain
from jx_base.expressions.literal import NULL
from jx_python import windows
from jx_python.expressions import jx_expression_to_function
from mo_collections.matrix import Matrix
from mo_dots import to_data
from jx_base.utils import coalesce, enlist
from mo_logs import Log
from mo_math import UNION
from mo_times.dates import Date

_ = Date


def is_aggs(query):
    if query.edges or query.groupby or any(s.aggregate is not NULL for s in query.select.terms):
        return True
    return False


def list_aggs(frum, query):
    frum = to_data(frum)
    select = enlist(query.select)

    for e in query.edges:
        if isinstance(e.domain, DefaultDomain):
            accessor = jx_expression_to_function(e.value)
            unique_values = set(map(accessor, frum))
            if None in unique_values:
                e.allowNulls = coalesce(e.allowNulls, True)
                unique_values -= {None}
            e.domain = SimpleSetDomain(partitions=list(sorted(unique_values)))
        else:
            pass

    s_accessors = [(ss.name, jx_expression_to_function(ss.value)) for ss in select]

    result = {
        s.name: Matrix(
            dims=[len(e.domain.partitions) + (1 if e.allowNulls else 0) for e in query.edges],
            zeros=lambda: windows.name_to_aggregate.get(s.aggregate)(**s),
        )
        for s in select
    }
    where = jx_expression_to_function(query.where)
    coord = [None] * len(query.edges)
    edge_accessor = [(i, make_accessor(e)) for i, e in enumerate(query.edges)]

    net_new_edge_names = set(to_data(query.edges).name) - UNION(e.value.vars() for e in query.edges)
    if net_new_edge_names & UNION(ss.value.vars() for ss in select):
        # s_accessor NEEDS THESE EDGES, SO WE PASS THEM ANYWAY
        for d in filter(where, frum):
            d = d.copy()
            for c, get_matches in edge_accessor:
                coord[c] = get_matches(d)

            for s_name, s_accessor in s_accessors:
                mat = result[s_name]
                for c in itertools.product(*coord):
                    acc = mat[c]
                    for e, cc in zip(query.edges, c):
                        d[e.name] = e.domain.partitions[cc]
                    val = s_accessor(d, c, frum)
                    acc.add(val)
    else:
        # FASTER
        for d in filter(where, frum):
            for c, get_matches in edge_accessor:
                coord[c] = get_matches(d)

            for s_name, s_accessor in s_accessors:
                mat = result[s_name]
                for c in itertools.product(*coord):
                    acc = mat[c]
                    val = s_accessor(d, c, frum)
                    acc.add(val)

    for s in select:
        # if s.aggregate == "count":
        #     continue
        m = result[s.name]
        for c, var in m.items():
            if var != None:
                m[c] = var.end()

    from jx_python.containers.cube import Cube

    output = Cube(select, query.edges, result)
    return output


def make_accessor(e):
    d = e.domain
    # d = _normalize_domain(d)
    if e.value:
        accessor = jx_expression_to_function(e.value)
        if e.allowNulls:

            def output1(row):
                return [d.getIndexByKey(accessor(row))]

            return output1
        else:

            def output2(row):
                c = d.getIndexByKey(accessor(row))
                if c == len(d.partitions):
                    return []
                else:
                    return [c]

            return output2
    elif e.range:
        for p in d.partitions:
            if p["max"] == None or p["min"] == None:
                Log.error("Inclusive expects domain parts to have `min` and `max` properties")

        mi_accessor = jx_expression_to_function(e.range.min)
        ma_accessor = jx_expression_to_function(e.range.max)

        if e.range.mode == "inclusive":

            def output3(row):
                mi, ma = mi_accessor(row), ma_accessor(row)
                output = [p.dataIndex for p in d.partitions if mi <= p["max"] and p["min"] < ma]
                if e.allowNulls and not output:
                    return [len(d.partitions)]  # ENSURE THIS IS NULL
                return output

            return output3
        else:

            def output4(row):
                mi, ma = mi_accessor(row), ma_accessor(row)
                var = d.key
                output = [p.dataIndex for p in d.partitions if mi <= p[var] < ma]
                if e.allowNulls and not output:
                    return [len(d.partitions)]  # ENSURE THIS IS NULL
                return output

            return output4
