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

## 3. `union` aggregate has no Python interpretation (PARTLY FIXED)

`jx_base.UnionOp` was reworked into a single-`frum` decisive set-union aggregate (to fix
`test_agg_ops.py::test_union` on sqlite). Only the sqlite backend implemented it
(`jx_sqlite/aggregates.py::_union_aggregate` → `JSON_GROUP_ARRAY(DISTINCT ...)`).

**Done:** the expression itself now evaluates in jx_python — `UnionOp.__call__` (distinct,
non-null values of `frum`, as a set) and `jx_python/expressions/union_op.py to_python`;
`partial_eval` now returns `lang.UnionOp` as the language invariant requires. Covered by
`tests/test_expressions.py test_union` / `test_union_of_one_value` (interpreted + compiled).

**Still open:** `{"aggregate": "union"}` now works in a query too (the groupby/value paths
run the aggregate expressions directly — `windows.name_to_aggregate` is no longer consulted),
but the `edges` form still dies in the cube path (#4). Nested/multi-value union coverage
(mirror the skipped `test_edge_1.py::test_union_*`) is still missing.

## 4. `list_aggs`: edges/cube path still expects the old normalized-select dicts (PARTLY FIXED)

`containers/lists/aggs.py list_aggs()` started with `select = enlist(query.select)`, but
`query.select` is a `SelectOp`; `enlist` iterates it into tuples, so `ss.name` raised
`AttributeError: 'tuple' object has no attribute 'name'` — every `edges`/`groupby` query
through `ListContainer.query` died there.

**Done:** the two paths the shared suite exercises in `list` format are ported to the
SelectOp model and no longer touch `windows.py`:
- `groupby_aggs` — groups the surviving rows by the groupby accessors, then runs each select
  term's aggregate over its group's values.
- `value_aggs` — no edges and no groupby is one group; returns the lone unnamed value (or an
  object of the named aggregates) with `meta.format "value"`.
Both lean on the aggregates being *collection ops* (`agg.__class__(frum=Literal(values))()`),
which is why min/max/avg/sum/union needed their `__call__` (see git log).

**Still open:** the `edges` path (`list_aggs` proper) is untouched — it still builds a `Cube`
of `Matrix` from `windows.name_to_aggregate.get(s.aggregate)(**s)`, which wants a *string*
aggregate name and a Data-like `s`. Porting it means deciding how edges/domains produce cube
coordinates under the SelectOp model, and teaching `Cube` about `SelectOne`. That blocks
`test_edge_*`, most of `test_agg_ops`' cube expectations, and
`test_filters.py test_edges_and_{empty,null}_prefix`.

## 5. `SelectOp.__data__` crashes when `frum` is a Schema (UNFIXED)

`jx_base/expressions/select_op.py __data__()` calls `symbiotic(SelectOp, self.frum, ...)`,
which reads `frum.precedence`; after `QueryOp.wrap` the `frum` of the normalized select is a
`Schema`, so `repr()` of any wrapped query's select raises
`AttributeError: 'Schema' object has no attribute 'precedence'`. Only hurts debugging/error
messages today (nothing in the suite prints one), which is why no test pins it.

## 6. `partial_eval` handed back JX ops to the Python language (FIXED)

Three separate ways an expression lost its language on the way through `partial_eval`, all of
which end at `language.partial_eval`'s `expecting Python`, or worse at a JX op with no
`to_python`:

- the collection aggregates (`CountOp`, `MinOp`, `MaxOp`, `SumOp`, `ProductOp`, `AvgOp`) built
  themselves in `__new__` with `object.__new__(CountOp)` — the hard-coded jx_base class, so
  `lang.CountOp(...)` produced a *JX* op. Now `object.__new__(cls)`.
- their `partial_eval` returned `MinOp(frum=...)` etc. instead of `lang.MinOp(frum=...)`.
- `Expression.invert` (the default) returned `NotOp(better)`, and
  `StrictEqOp.partial_eval`'s `x == 0 -> not x` rewrite returned `NotOp(lhs)`; both now use
  `lang.NotOp`.

The `x == 0 -> not x` rewrite depends on a second, fragile mechanism: it *mutates*
`lhs._jx_type = JX_BOOLEAN` so that `NotOp.to_python`'s `ToBooleanOp(term).partial_eval`
collapses and the host's own truthiness (`not 0`) decides. That only survives because a
`simplified` op of the right `lang` is returned as-is by the `partial_eval` dispatcher — with
the language lost, the op was rebuilt and the instance's `_jx_type` went back to
`JX_INTEGER`, re-inserting `exists(f) and f is not False`, which is True for `0`. So
`{"eq": [{"count": "arr"}, 0]}` silently matched nothing on the compiled harness.

Covered by `tests/test_jx/test_filters.py test_where_count_empty_collection` (which came in
from SVN failing) and `tests/test_expressions.py
test_aggregate_partial_eval_stays_in_language`.

**Still open:** `jx_python/expressions/avg_op.py` is not registered in
`jx_python/expressions/__init__.py`, and cannot be — its `to_python` is dead code from the
pre-`frum` AvgOp (it reads `self.default`/`self.terms`, assigns `to_python` twice, and imports
a `PythonSource` that `_utils` does not export). `avg` therefore has no compiled path at all;
only the interpreted `AvgOp.__call__` works. `ProductOp` had the same registration gap and is
now wired up.
