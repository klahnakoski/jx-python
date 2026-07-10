# jx_python — known defects (found 2026-07-09, jx-sqlite repair campaign)

Found while restoring the jx-sqlite test baseline (see jx-sqlite `docs/TEST_TRIAGE.md`).
The suite there now passes 142 / errors 62 / skips 147; the items below are the jx_python
share of the remaining errors, plus fixes already applied that need to survive the next
lib sync. Each item states what was verified vs. suspected.

> STATUS 2026-07-10: #1 FIXED (confirmed in source + coverage), #2 FIXED, #3 FIXED on the
> jx_python side (root-cause leak still downstream), #4 jx.tuple(FlatList) FIXED; the rest of
> #4 is jx-sqlite-side or an unbuilt feature. Details under each item.

## 1. `jx.sort` lost its default sort-by-value (FIXED in jx-sqlite; keep upstream)

**FIXED:** escape hatch confirmed present in source `jx_python/jx.py`; coverage in
`tests/test_sort.py`. Also fixed `jx_base/expressions/sort_op.py` (used `is_integer`/`Log`
without importing them, crashing the `{"field":..,"sort":-1}` form).

The rewrite of `jx.py sort(frum, *sorts)` dropped the old no-fieldnames branch. Two
consequences, both verified:

- With no sorts, `all(isinstance(s, SortOne) for s in ())` is vacuously true, so
  normalization is skipped, `funcs = []`, the comparer returns 0 for every pair, and
  `sorted()` is a stable no-op — data returned in input order (arbitrary for a set).
  Silent wrong order, no error.
- Before that can even happen, `Container.create(frum)` crashes on plain scalar data
  (see item 2), so `jx.sort({"a", "b"})` raised instead of sorting.

Fix applied (jx-sqlite commit `e2f9d96`), restoring the old escape hatch ahead of
container creation:

```python
if frum == None:
    return Null
if not sorts:
    return to_data(sort_using_cmp(frum, value_compare))
```

Verified: `jx.sort([3, None, 'b', 1, 'a'])` → `[1, 3, 'a', 'b', Null]`.
**This lives in vendored `jx_python/jx.py` in jx-sqlite — it must be applied at the
source repo or the next sync reverts it.**

Coverage to add: no-arg sort of list/set/FlatList; mixed types; None in data; single
fieldname; `{"field": ..., "sort": -1}` form; empty input; None input.

## 2. `Container.create` on scalar lists → invalid Column (FIXED)

**FIXED:** the `Column` constraint now permits a primitive `json_type` at `es_column="."`
(nameless scalar list), matching the dynamically-typed python target; tests in
`tests/test_lists.py`. list-of-lists is intentionally out of scope (see `jx_base/CLAUDE.md`).

`Container.create([1, 2, 3])` (or any list/set of scalars) → `ListContainer.__init__`
→ `get_schema_from_list` builds `Column(es_column=".", json_type="string"/"number")`,
which violates the Column constraint `when es_column == "." then json_type in
["nested", "object"]` → ValueError. Any code path that wraps scalar data in a
container is affected; item 1's fix merely routes the common `jx.sort` case around it.

Coverage to add: `get_schema_from_list` over scalars, list-of-lists, and mixed
scalar/object data.

## 3. `python_type_to_json_type` receives expression objects (jx_python side FIXED)

**FIXED (jx_python side):** `get_schema_from_list` now treats a jx `NULL` literal as missing
(via `_jx_type is JX_IS_NULL`) instead of hard-failing the whole container; tests in
`tests/test_lists.py`. The root-cause leak (a `NullOp` reaching result rows) is still
downstream in jx-sqlite edge queries.

`mo_json.types.python_type_to_json_type` errors "not expected NullOp" when schema
inference meets a row containing a jx_base `NULL` (NullOp) instance. The leak is in
jx-sqlite edge-query result rows (suspect: edge-domain pulls / `domain.getKeyByIndex`
partition values), not in jx_python — but `get_schema_from_list` currently turns one
bad value into a hard failure for the whole container. 46 of jx-sqlite's 62 remaining
errors share this signature; `test_edge_1.test_count_constant` is a small reproducer.

## 4. Unverified leads (from remaining jx-sqlite error tail)

- `TypeError: 'FlatList' object is not callable` (2 tests) — somewhere a FlatList is
  used where a pull/callable is expected.
- `AttributeError: 'ListContainer' object has no attribute 'get_id'` (1 test).
- `jx.py tuple()` raises "not supported yet" for Cube and FlatList inputs.
  **FlatList FIXED** (`tests/test_tuple.py`); **Cube** remains genuinely unimplemented (feature).

STATUS of the other two leads: `'FlatList' not callable` and `'ListContainer' has no get_id`
are jx-sqlite-side symptoms — the calling code is not in jx_python (all `.get_id()` here is on
Expression ops), so they are not reproducible or fixable in this repo.

## Context

jx-sqlite's harness and monolith query path were restored to the pre-2025-03 shape
(jx-sqlite commit `4d456c3`): `QueryOp` normalization is back (from `32a1736`) and
`tests/__init__.py` calls `table.query` again. The `Container.query` expression-algebra
path was left in place but has no coverage; jx_python changes should be tested against
the jx-sqlite suite (`PYTHONPATH=.;vendor`, `py -m unittest discover -s tests`).
