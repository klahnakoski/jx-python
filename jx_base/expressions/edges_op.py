# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.domains import DefaultDomain, Domain, SetDomain
from jx_base.expressions._utils import jx_expression, _jx_expression
from jx_base.expressions.expression import Expression
from jx_base.utils import delist
from jx_base.utils import enlist
from mo_dots import list_to_data, is_container
from mo_future import is_text
from mo_imports import expect
from mo_logs import Log

Column = expect("Column")


class OneEdge:
    def __init__(
        self,
        frum,
        *,
        name,
        value,
        allowNulls,
        dim,
        domain
    ):
        self.frum = frum
        self.name = name
        self.value = value
        self.allowNulls = allowNulls
        self.dim = dim
        self.domain = domain


class EdgesOp(Expression):
    def __init__(self, frum, *edges):
        Expression.__init__(self, frum)
        self.frum = frum
        self.edges = edges

    @classmethod
    def define(cls, expr):
        raw_frum, *raw_edges = expr["edges"]
        frum = _jx_expression(raw_frum, cls.lang)
        edges = _normalize_edges(frum, raw_edges, limit=None, schema=None)
        return EdgesOp(frum, *edges)


def _normalize_edges(frum, edges, limit=None, schema=None):
    if not schema:
        schema = frum.schema
    return list_to_data([
        n for ie, e in enumerate(enlist(edges)) for n in _normalize_edge(frum, e, ie, limit=limit, schema=schema)
    ])


def _normalize_edge(frum, edge, dim_index, limit, schema):
    """
    :param edge: raw edge
    :param dim_index: Dimensions are ordered; this is this edge's index into that order
    :param schema: for context
    :return: a normalized edge
    """
    if not edge:
        Log.error("Edge has no value, or expression is empty")
    elif is_text(edge):
        if schema:
            leaves = delist([l for r, l in schema.leaves(edge)])
            if not leaves or is_container(leaves):
                return [OneEdge(
                    frum=frum,
                    name=edge,
                    value=jx_expression(edge),
                    allowNulls=True,
                    dim=dim_index,
                    domain=_normalize_domain(None, limit),
                )]
            elif isinstance(leaves, Column):
                return [OneEdge(
                    frum=frum,
                    name=edge,
                    value=jx_expression(edge),
                    allowNulls=True,
                    dim=dim_index,
                    domain=_normalize_domain(domain=leaves, limit=limit, schema=schema),
                )]
            elif is_list(leaves.fields) and len(leaves.fields) == 1:
                return [OneEdge(
                    frum=frum,
                    name=leaves.name,
                    value=jx_expression(leaves.fields[0]),
                    allowNulls=True,
                    dim=dim_index,
                    domain=leaves.getDomain(),
                )]
            else:
                return [OneEdge(name=leaves.name, allowNulls=True, dim=dim_index, domain=leaves.getDomain(),)]
        else:
            return [OneEdge(
                frum=frum,
                name=edge, value=jx_expression(edge), allowNulls=True, dim=dim_index, domain=DefaultDomain(),
            )]
    else:
        edge = to_data(edge)
        if not edge.name and not is_text(edge.value):
            Log.error("You must name compound and complex edges: {edge}", edge=edge)

        if is_container(edge.value) and not edge.domain:
            # COMPLEX EDGE IS SHORT HAND
            domain = _normalize_domain(schema=schema)
            domain.dimension = OneEdge(fields=edge.value)

            return [OneEdge(
                frum=frum,
                name=edge.name,
                value=jx_expression(edge.value),
                allowNulls=bool(coalesce(edge.allowNulls, True)),
                dim=dim_index,
                domain=domain,
            )]

        domain = _normalize_domain(edge.domain, schema=schema)

        return [OneEdge(
            frum=frum,
            name=coalesce(edge.name, edge.value),
            value=jx_expression(edge.value) if edge.value else None,
            range=_normalize_range(edge.range),
            allowNulls=bool(coalesce(edge.allowNulls, True)),
            dim=dim_index,
            domain=domain,
        )]


class OneRange:
    def __init__(self, min, max, mode):
        self.min = min
        self.max = max
        self.mode = mode


def _normalize_range(range):
    if range == None:
        return None

    return OneRange(
        min=jx_expression(range.min),
        max=jx_expression(range.max),
        mode=range.mode,
    )


def _normalize_domain(domain=None, limit=None, schema=None):
    if not domain:
        return DefaultDomain(limit=limit)
    elif isinstance(domain, Column):
        if (
            domain.partitions and domain.multi <= 1
        ):  # MULTI FIELDS ARE TUPLES, AND THERE ARE TOO MANY POSSIBLE COMBOS AT THIS TIME
            return SetDomain(partitions=domain.partitions.limit(limit))
        else:
            return DefaultDomain(limit=limit)
    elif isinstance(domain, Dimension):
        return domain.getDomain()
    elif schema and is_text(domain) and schema[domain]:
        return schema[domain].getDomain()
    elif isinstance(domain, Domain):
        return domain

    return Domain(domain)
