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

**Done (2026-07-30):** `{"aggregate": "union"}` works on every path — groupby, value, and
`edges` (#4). A union *of collections* is flat: `UnionOp.__call__` and its `to_python` used to
build `set(...)` straight from the collection, so a multi-valued member raised
`TypeError: unhashable type: 'list'`. One cell of an `edges` query is exactly that shape (a
value per row, each possibly multi-valued). Covered by `tests/test_expressions.py
test_union_of_collections` (interpreted + compiled), `tests/test_jx/test_agg_ops.py
test_union_of_multivalue`, and the unskipped `test_edge_1.py::test_union_*`.

## 4. `list_aggs`: edges/cube path still expects the old normalized-select dicts (FIXED)

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

**Done (2026-07-30, docs/SHAPING_PLAN.md Phase 1):** the `edges` path is ported. The cube is
the working structure — one `Matrix(dims=dims, zeros=list)` per select term, so every
coordinate exists (with its own list) before any data arrives; one pass appends each row's
value into the cells it belongs to (`itertools.product(*coord)` fans a multi-valued edge out);
then each cell is aggregated in place by `_aggregate`, the same helper `groupby_aggs`/
`value_aggs` use. `windows.py` is out of the path entirely. What the plan did *not* survive:

- **The output is rows, not a `Cube`.** The `test_jx` harnesses are list-only
  (`tests/harness.py supported_formats`), and `list_container.py:139` hands back `output.data`
  — for a `Cube` that is a dict of `Matrix`, not rows. `_cube_to_rows` emits one row per
  coordinate, empty cells included (`test_where_w_dimension` expects `{"a": "b"}` with no
  aggregate value, `test_edge_limit_big` expects the empty `allowNulls` row). Building a
  `Cube` as well would be code no test can reach — see "still open" below.
- **An aggregate is a declaration over a group, not an expression over one document.** An
  empty group reports nothing even for `sum`, whose decisive form is total at 0
  (`test_edge_2.test_sum_rows` wants `NULL`; `tests/test_expressions.py` still pins
  `{"sum": "a"}` over a document with no `a` at 0). `count`/`cardinality` of an empty group
  really is 0. A `default` on the select term fills the hole *before* the aggregate runs, or
  `test_edge_1.test_sum_default` never sees its `-1`.
- **Partition `where` filters are a `case`, not a set:** the first partition a row matches
  claims it (`test_edge_w_partition_filters`: 3 + 4 + 6 rows over 13, no double counting).
- **Domains are inferred into a side list**, not mutated into `query.edges`, and are sorted
  with `value_compare` (`sorted()` dies on a tuple holding a null) and truncated by
  `domain.limit`, which sends the leftovers to the `allowNulls` part.

`test_edge_1` 37/40, `test_edge_2` 4/7, `test_edge_time` 2/2, `test_time_domain` 6/8 on both
harnesses (was 3/40, 0/7, 0/2, 4/8). Still open:

- `format: "cube"`/`"table"` for an aggregate query is **unshaped**: `list_aggs` returns rows,
  and `list_container.py:141-156` then treats them as a `rownum` cube. No harness asks for
  those formats, so there is nothing to test against — teaching `PythonHarness` to produce
  `table` is the prerequisite, not more code in `list_aggs`.
- a **tuple edge** gets an extra empty `allowNulls` row (`test_edge_using_tuple` produces 9
  rows for 8 expected — the tuple `[NULL, NULL]` is already a partition, so the null slot is
  redundant). The test passes only because `assertAlmostEqual` pairs a trailing extra row
  against a missing expectation and returns. jx_sqlite's `format.py` has the same
  `is_op(e.value, TupleOp)` special case and also keeps the slot; the *list* expectation says
  otherwise. Kyle: does a tuple edge have a null part?
- `test_edge_1`: `test_percentile` (no `PercentilesOp` anywhere — sqlite skips it too),
  `test_edge_using_between` (`between` is broken), `test_shallow_with_deep_edge` (Phase 3).

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

## 7. arithmetic could not be compiled at all (FIXED)

`jx_expression_to_function` calls `to_python()` with no arguments, and every op's `to_python`
takes `loop_depth=0` — except the two shared helpers assigned directly as `to_python`:
`_binaryop_to_python` (`sub`/`pow`/`mod`) and `multiop_to_python` (`add`/`mul`/`avg`/`stats`/
`percentile`) took it positionally. So `{"sub": ["a", "b"]}` as an edge or select *value* raised
`TypeError: _binaryop_to_python() missing 1 required positional argument`. It hid behind
constant folding: `{"sub": [1, 2]}` never reaches the helper. Covered by
`tests/test_expressions.py test_arithmetic_over_variables_compiles`, and by the unskipped
`test_edge_1.py::test_expression_on_edge` / `test_edge_w_expr_and_domain`.

## 8. `_normalize_edge` drops the query's `limit` for a written-out domain (WORKED AROUND)

`jx_base/expressions/query_op.py _normalize_edge` is handed `limit` so an inferred domain knows
how many parts to keep, and forwards it for a bare `edges: ["k"]` — but the `is_data(edge)`
branch calls `_normalize_domain(edge.domain, schema=schema)` without it, so
`{"value": "k", "domain": {"type": "default"}}` under `"limit": 5` gets no limit at all
(`test_edge_1.test_general_limit`). `_resolve_domains` in jx_python falls back to `query.limit`
rather than changing jx_base, because jx_base is the SVN channel jx_sqlite shares and sqlite
passes that test by its own route; fix belongs upstream once both backends can be run.

## 9. two vendored gaps the edges path walked into (FIXED in `vendor/`, needs svn-sync)

- `mo_collections.matrix._getitem` could not index a **zero-dimensional** cube: `Matrix(dims=[])`
  holds exactly one cell (the cube *is* the cell — `m[()]` and `m[()] = v` already worked), but
  `items()` passed the empty coordinate to `_getitem`, which read `i[0]` → `IndexError`. Reached
  by `format: "cube"`/`"table"` with no edges (`list_container.py:120` only diverts
  `format in (None, "list")` to `value_aggs`). Covered by `tests/test_lists.py
  test_zero_edge_aggregate_is_one_cell`.
- `mo_json.types.python_type_to_json_type` knew `Data` but not `FlatList` (nor `tuple`), so
  schema inference over rows holding a `FlatList` — which is what a tuple edge's domain key is —
  raised `not expected FlatList`. Its `is_data`/`is_many` fallbacks test *instances*, and it is
  handed a class.
