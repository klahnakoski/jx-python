# jx_python — known defects

## 1. `jx.sort(frum, *sorts)` required schema inference just to sort (FIXED in jx-sqlite vendored copy — needs upstream + tests)

`sort` wrapped `frum` in `Container.create(frum)` solely to normalize the sort spec via
`jx_expression({"from": frum, "sort": sorts})`, and returned a `ListContainer`. Two verified
problems (2026-07-10, jx-sqlite harness):

- `Container.create` runs `get_schema_from_list` over the data, which hard-fails on rows
  holding opaque values — predicate functions ("not expected function"), `Duration`
  ("not expected Duration"), `Data`-wrapped scalars ("'str' object has no attribute 'items'").
  Sorting needs a comparer, not a schema.
- The `ListContainer` return contradicts the docstring ("A NEW LIST OF DATA") and the
  no-sorts branch (returns `to_data` list); a caller assigning the result into a Data slot
  gets `{"data": [...], "meta": {...}}` instead of the rows.

**Fix applied:** normalize each sort with `jx_base.expressions.sort_op._normalize_sort`
(no container needed; SortOne.expr expressions are row-callable), skip `Container.create`,
return `to_data(sorted_rows)`. Existing upstream tests already consume the result with
`list(...)`, so the return-type change is compatible.

Coverage to add upstream: sort data containing arbitrary/unsortable objects (functions,
Duration); sort a list of strings by `"."` (also `[".", "."]`); sort spec items wrapped in
`Data` (see jx_base note on `_normalize_sort`); result of `jx.sort(data, fields)` is
list-like, not a container.

## 2. `ListContainer.sort` passes stale `already_normalized=True` (UNFIXED lead)

`containers/list_container.py sort()` calls `jx.sort(self.data, sort, already_normalized=True)`
— that keyword was dropped from `jx.sort`'s signature in the rewrite, so any sorted query
through `ListContainer.query` raises TypeError. No jx-sqlite test currently exercises it
(suite green without touching it); left unfixed pending a test that pins the intended `sort`
argument shape (list of SortOne from QueryOp normalization, presumably `jx.sort(self.data,
*sort)`).
