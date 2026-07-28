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

## 2. `ListContainer.sort` passes stale `already_normalized=True` (UNFIXED lead)

`containers/list_container.py sort()` calls `jx.sort(self.data, sort, already_normalized=True)`
— that keyword was dropped from `jx.sort`'s signature in the rewrite, so any sorted query
through `ListContainer.query` raises TypeError. No jx-sqlite test currently exercises it
(suite green without touching it); left unfixed pending a test that pins the intended `sort`
argument shape (list of SortOne from QueryOp normalization, presumably `jx.sort(self.data,
*sort)`).

## 3. `union` aggregate has no Python interpretation (UNFIXED — needs tests)

`jx_base.UnionOp` was reworked into a single-`frum` decisive set-union aggregate (to fix
`test_agg_ops.py::test_union` on sqlite). Only the sqlite backend implements it
(`jx_sqlite/aggregates.py::_union_aggregate` → `JSON_GROUP_ARRAY(DISTINCT ...)`); jx_python
has no `__call__`/compiled form for it, so a `{"aggregate": "union"}` query run over Python
objects would error or silently return nothing. Add a jx_python union test (flat scalar
column) and the interpretation to satisfy it; then nested/multi-value union coverage (mirror
the skipped `test_edge_1.py::test_union_*`).
