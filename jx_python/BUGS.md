# jx_python — known defects

## 1. `jx.sort(frum, *sorts)` required schema inference just to sort (FIXED — needs upstream + tests)

`sort` wrapped `frum` in `Container.create(frum)` (to normalize the sort spec) and returned a
`ListContainer`. `Container.create` runs `get_schema_from_list`, which hard-fails on opaque
rows (functions, `Duration`, Data-wrapped scalars) — sorting needs a comparer, not a schema;
and the container return contradicts the docstring/no-sorts branch. Fix: normalize each sort
with `sort_op._normalize_sort` (no container; SortOne.expr is row-callable), skip
`Container.create`, return `to_data(sorted_rows)`.
Coverage: sort data with unsortable objects (functions, Duration); sort strings by `"."` (and
`[".", "."]`); Data-wrapped sort items; result is list-like, not a container.

## 2. `ListContainer.sort` passed stale `already_normalized=True` (FIXED)

`containers/list_container.py sort()` called `jx.sort(self.data, sort, already_normalized=True)`
— that keyword was dropped from `jx.sort`'s signature in the rewrite, so any sorted query
through `ListContainer.query` raised TypeError.

**Fix applied:** `jx.sort(self.data, *enlist(sort))` — `query.sort` is already a list of
`SortOne` from QueryOp normalization, and `jx.sort` passes those through untouched.
Covered by `tests/test_jx/test_filters.py test_where_expression` (any test with a `sort`
clause on the `python`/`interpret` harnesses).

## 3. `union` aggregate has no Python interpretation (UNFIXED — needs tests)

`jx_base.UnionOp` was reworked into a single-`frum` decisive set-union aggregate (to fix
`test_agg_ops.py::test_union` on sqlite). Only the sqlite backend implements it
(`jx_sqlite/aggregates.py::_union_aggregate` → `JSON_GROUP_ARRAY(DISTINCT ...)`); jx_python
has no `__call__`/compiled form for it, so a `{"aggregate": "union"}` query run over Python
objects would error or silently return nothing. Add a jx_python union test (flat scalar
column) and the interpretation to satisfy it; then nested/multi-value union coverage (mirror
the skipped `test_edge_1.py::test_union_*`).

## 4. `list_aggs` still expects the old normalized-select dicts (UNFIXED)

`containers/lists/aggs.py list_aggs()` starts with `select = enlist(query.select)`, but
`query.select` is now a `SelectOp`; `enlist` iterates it into tuples, so `ss.name` raises
`AttributeError: 'tuple' object has no attribute 'name'` — every `edges`/`groupby` query
through `ListContainer.query` dies there. The terms are `query.select.terms` (a list of
`SelectOne`, each with `.name`, `.value`, `.aggregate`), but that is only the first line:
`windows.name_to_aggregate.get(s.aggregate)(**s)` also wants a *string* aggregate name and a
Data-like `s`, and `Cube(select, edges, result)` downstream has the same assumption. So the
whole edges/cube path needs porting to the SelectOp model, not a one-line fix.

Blocks `test_filters.py test_edges_and_empty_prefix` / `test_edges_and_null_prefix`, and is
almost certainly why `test_edge_*`, `test_groupby_*` and `test_agg_ops` are skipped wholesale
on the python/interpret harnesses.

## 5. `SelectOp.__data__` crashes when `frum` is a Schema (UNFIXED)

`jx_base/expressions/select_op.py __data__()` calls `symbiotic(SelectOp, self.frum, ...)`,
which reads `frum.precedence`; after `QueryOp.wrap` the `frum` of the normalized select is a
`Schema`, so `repr()` of any wrapped query's select raises
`AttributeError: 'Schema' object has no attribute 'precedence'`. Only hurts debugging/error
messages today (nothing in the suite prints one), which is why no test pins it.
