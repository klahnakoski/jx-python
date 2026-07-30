# What jx_python should borrow from jx_sqlite — and what it must not

Written 2026-07-29, after reading `jx-sqlite/jx_sqlite/{builder,edges,domain,group,aggregates,
format}.py` and `jx-sqlite/docs/INTERSECTION_SURVEY.md`.

## Verdict

Kyle's hedge is half right, and the two halves split cleanly along jx_sqlite's own sub-problem
list (`INTERSECTION_SURVEY.md §1`):

- **Borrow P7 (the pull plan / result shaping) outright.** It is *not SQL at all* — the survey
  says so itself: "PullPlan — not SQL at all: the declarative inverse of SqlHierarchy... This
  wants to be its own module regardless of what happens above it." `jx_sqlite/format.py`
  already implements it, against **byte-identical** shared test files, and it reads nothing
  sqlite-specific. jx_python currently has a second, weaker implementation of the same job.
- **Do not borrow P2/P3/P4/P5 (join chain, aligned select lists, branch UNION, order
  recovery), nor `BranchBuilder`.** Every one of those exists to squeeze a hierarchical answer
  through SQL's flat rectangular interface. Python has no such interface. Recursing into the
  data is not just easier — it makes whole classes of jx_sqlite complication *evaporate*
  (see "What disappears in Python" below).
- **Borrow exactly one idea from P6b (`sql_complete`): materialize the dense coordinate space
  first, then fill it.** That is `itertools.product` in Python, and it settles the design fork
  I raised earlier (Matrix accumulator vs. whole-collection aggregate) in favour of the
  simpler answer.

So: steal the *back* of the pipeline, ignore the *middle*, and steal one trick from the front.

## Evidence

| claim | check |
|---|---|
| the two repos run the same expectations | `diff -q tests/test_jx/test_edge_1.py` across repos → identical |
| sqlite already satisfies the cube expectations jx_python fails | `test_edge_1`: 40 tests, 4 sqlite-skips (36 run) vs 37 python-skips (3 run). `test_deep_ops`: 50 tests, 5 sqlite-skips (45 run) vs 47 python-skips (3 run) |
| one bug blocks the whole edges path here | unskipping `test_edge_1` on jx_python → 36 errors, 58 hits of `'tuple' object has no attribute 'name'` from `containers/lists/aggs.py:41` |
| one bug blocks the whole deep path here | unskipping `test_deep_ops` → 47 errors; 40 of them hit `This container only has table by name of …` (`containers/list_container.py:301`) |
| `jx_base` is a shared channel, not a copy | same SVN URL `https://kyle-win11/svn/pyLibrary/jx_base` in both repos (r2884 here, r2881 in `jx-sqlite/vendor/jx_base`). `join_vars()` reached this repo that way on 2026-07-29 |
| the dependency direction allows sharing | jx-sqlite vendors jx_python and `format.py` does `from jx_python import jx`; `jx_base/__init__.py:28` already imports `jx_python.expressions._utils.Python`. Nothing new is needed |
| `format.py` is language-neutral | `format_flat`/`format_deep` read only flat rows plus `ColumnMapping.{is_edge, num_push_columns, push_list_name, push_column_child, push_column_index, push_column_name, push_column_path, push_column_slot, slot_path, pull, nested_path}`. The `sql` field is **never read**. `ColumnMapping` is built with `jx_base.data_class.DataClass` already |

## What jx_python has today

- `containers/lists/aggs.py`
  - `groupby_aggs`, `value_aggs` — ported to the `SelectOp` model; they aggregate by calling
    `agg.__class__(frum=Literal(values))()`, i.e. **one aggregate op over one collection**.
  - `list_aggs` (the edges path) — untouched. Dies at line 41 (`enlist(query.select)` yields
    tuples), then would die at line 59 (`windows.name_to_aggregate.get(s.aggregate)(**s)`
    wants a *string* aggregate name and a Data-like `s`), then at line 106 (`Cube` knows
    nothing of `SelectOne`).
- `containers/list_container.py:138-157` — its own `format` list/table/cube, deriving headers
  from `schema.snowflake.columns`. This is an independent, weaker re-do of `format_deep`.
- `containers/list_container.py:293-301` — `get_snowflake`/`get_table` accept only the
  container's own name. One flat table by construction ("A CONTAINER WITH ONLY ONE TABLE").
- Schema inference is further along than the container is: for
  `[{"o": 1, "a": [{"b": 1}, {"b": 2}]}]` the snowflake already holds
  `('b', 'a.b', ['a', '.'])` and `query_paths == ['.', 'a']`. But
  `snowflake.get_schema('a')` returns **no columns**, and `get_schema_from_list("testdata", …)`
  on nested data raises the `{"not": {"prefix": [{"first": "nested_path"}, {"literal":
  "testdata"}]}}` constraint (the harness dodges this by naming the container `"."`).

## What disappears in Python (why the middle must not be copied)

jx_sqlite carries three pieces of machinery that exist *only* because SQL joins duplicate rows
and cannot return a hierarchy:

1. `aggregate_frame` / `frames_one_document` / `per_document_aggregates` (`edges.py:86-110`) —
   the "implicit document edge": a two-level query so that `sum(v)` over an **ancestor's**
   value does not count the copies the join chain made of it. In Python there are no copies:
   recursing into `row["a"]` visits each child once and the parent stays one object. This
   entire concept has no jx_python analogue and must not acquire one.
2. `sql_join_chain` + `__order__ = 0` (inner object as a one-element array) — the data already
   *is* nested; `enlist`/`delist` is the whole rule.
3. `BranchBuilder` / `DocumentDetails` / aligned select lists / UNION ALL branches — assembling
   one flat rectangle that can be folded back. Python skips the fold: build the nested answer
   directly.

`DocumentDetails.slot_path`/`slot_columns` ("TWO SIDE TABLES, NOT A NODE PER TERM") is still
worth reading as a *modelling* example — it is the column-wise style — but not as code to port.

## Plan

### Phase 1 — edges, as a dense coordinate space (unblocks `test_edge_1`, `test_edge_2`, `test_edge_time`, `test_time_domain`, the cube half of `test_agg_ops`)

Rewrite `list_aggs` in `containers/lists/aggs.py` as five steps, no `windows.py`, no
incremental accumulator:

1. **Domains.** Keep the existing `DefaultDomain` inference (lines 43-52) but stop mutating
   `query.edges[i].domain` in place — build a side list `domains[i]`. `QueryOp.wrap` normalizes
   edges; the direct `ListContainer.query(...)` path does not, which is why a raw
   `edges: ["a"]` currently fails with `'str' object has no attribute 'domain'`. Normalize (or
   refuse) at the entry, not inside the loop.
2. **Coordinate space.** `dims = [len(parts) + (1 if allowNulls else 0) …]`; the cell order is
   `itertools.product(*(range(d) for d in dims))` — which *is* cube order, the same invariant
   `format.py:133` relies on ("WORKS BECAUSE THE DATABASE SORTED THE EDGES TO CONFORM"). This
   is `sql_complete` without SQL: every coordinate exists before any data arrives, so empty
   cells need no special case.
3. **One pass, values into cells.** For each surviving row, `make_accessor` already yields the
   part indices per edge; for each `coord in itertools.product(*coords)` append each select
   term's value into `cells[coord][term]`.
4. **Aggregate per cell.** `agg.__class__(frum=Literal(values))()` — the identical call
   `groupby_aggs` already uses. Empty cell → the decisive default falls out for free
   (`count`→0, `sum`→0, `min`/`max`/`avg`→`NULL`; pinned by `tests/test_expressions.py`).
5. **Shape.** Emit `Matrix(dims=dims)` per select term for `format: "cube"`, or the flat
   coordinate rows for `list`/`table`. Phase 2 replaces this step with the shared formatter.

### Phase 2 — one shaping layer for both backends

Move `format_flat` + `format_deep` + `ColumnMapping` into **`jx_base`** (`jx_base/formatting.py`,
`ColumnMapping` beside `data_class.py`), have jx_sqlite import them, and delete
`list_container.py:138-157` in favour of the same call. Rationale: both are language-neutral,
`ColumnMapping` is already a `jx_base.data_class.DataClass`, and jx_base is the SVN channel both
repos share. Two small edits are needed on the way in: `jx.sort` → `sorted(..., key=cmp_to_key(
value_compare))` (`jx_base.language`), and `untype_field` is only reached for typed sqlite names
— jx_python keeps `es_column="."` (see `jx_base/CLAUDE.md`), so that branch is inert here.

Do Phase 2 **after** Phase 1, not before: Phase 1 tells us whether jx_python actually wants a
pull plan or can shape directly, and a wrong seam is more expensive than a duplicated
formatter.

### Phase 3 — nested tables (unblocks ~40 of `test_deep_ops`, most of `test_nested`)

`from: "testdata.a"` should give a container over the `a` sub-documents. Three ordered steps:

1. `Snowflake.get_schema("a")` returns no columns today even though the column
   `('b', 'a.b', ['a', '.'])` is there. Fix the perspective lookup first — it is a pure schema
   bug and independently testable.
2. `ListContainer.get_table(name)` — return a **view**: the flattened list of `a`
   sub-documents, each retaining a reference to its parent for up-reach (`o` from inside `a`).
   This is the Python replacement for `sql_join_chain`, and it is a recursion over the data,
   not a join.
3. Only then the deep `select` cases. `_top_name`/`_deep_header` in `format.py` encode which
   key a deep column lands under; that logic is worth borrowing verbatim once Phase 2 has moved
   it into jx_base.

Phase 3 is independent of Phases 1-2 and is the cheaper win per test unblocked; take it first
if the goal is test count rather than the shaping seam.

## Pre-mortems

- **Phase 1, most likely failure: double counting.** A multi-valued edge accessor, or
  `allowNulls`, puts one row into several cells (`itertools.product(*coord)`). Values must be
  appended *per coordinate*, not per row — get it backwards and every count in a multi-valued
  edge query is inflated. Pin it with a two-edge test where one edge is multi-valued before
  writing the loop.
- **Phase 1, second failure: `count` of rows vs `count` of values.** jx_sqlite needs two
  separate rules for this (`_count_records` counts the origin UID; `_count_columns` counts
  values wherever they live). A per-cell value list gives "count of values" for free but
  `{"aggregate": "count", "value": "."}` means *rows*. Decide it explicitly at step 3 — a cell
  needs its row count as well as its value lists.
- **Phase 2, most likely failure: the seam is wrong.** `format_flat` assumes the producer
  emitted one dense row per cell **in cube order**. If Phase 1's shaping turns out to want
  nested output directly (no flat intermediate), moving the formatter buys nothing and costs a
  jx_base API. That is the reason for the ordering above.
- **Phase 3, most likely failure: the parent link.** A view of `a` rows that carries its parent
  by reference makes up-reach trivial but aliases the data; any `update`/`window` that writes
  through the view mutates the fact. Read-only view, or copy — decide before step 2.

## Open questions for Kyle

1. `jx_sqlite/expressions/to_list_op.py` (`ToListOp`, built 2026-07-28) is described as "the
   one-column relation behind a collection… every collection operator is one `SqlAggregate`
   over one relation". jx_python reached the same shape from the other side: `ToArrayOp` plus
   `CountOp(frum=…)`/`MinOp(frum=…)`. Should these converge into one jx_base op, or are they
   deliberately separate (relation-valued vs. value-valued)?
2. Is `ColumnMapping` the right shared vocabulary, or is it already the *SQL-shaped* answer?
   Its `push_column_index`/`column_alias` fields exist because SQL returns positional rows.
   A Python producer would rather hand over `(name, path, getter)`. The survey's own caution
   applies: this induction comes from the code's drafts, not first principles.
3. `get_schema_from_list("testdata", nested_data)` raising the `nested_path`-prefix constraint
   is masked by the harness naming every container `"."`. Real bug, or is a named root simply
   not a supported shape?
