# jx_base — abstract JX language

Defines the reference JX language: one class per operator in `expressions/` (AddOp, EqOp,
MissingOp, …), plus the abstract data model in `models/` (Container → Namespace → Snowflake →
Facts/Table → Schema; see `models/README.md` for the nomenclature).

## The double-dispatch machinery (`language.py`) — read this before debugging any operator

- Every op class defined in `jx_base.expressions` gets a global `_op_id`. Other languages
  (Python, SQLang, JxSql) re-declare classes **with the same class name**; `register_ops(vars())`
  wires them into per-language lookup tables indexed by `Language.id`.
- Any method whose first two parameters are `(self, lang)` is a **double-dispatch method**
  (`partial_eval`, `missing`, …). `register_ops` **removes it from the class** and replaces it
  with a dispatcher. Consequence: in the debugger, `SomeOp.partial_eval` is NOT the code you
  wrote — the real method is in `cls.lookups["partial_eval"][lang.id]`
  (originals cached in `language._all_removed_methods`).
- A language that does not re-declare an op inherits the JX behavior via a synthesized subclass.
- Registration happens at the bottom of each language's `expressions/__init__.py`
  (`JX.register_ops(vars())`, etc.). **Trap:** a new op file does nothing until it is imported
  into that `__init__.py`; the class name must exactly match the jx_base class name.

## Invariants

- `partial_eval(lang)` must return an expression belonging to `lang` (literals exempt);
  `language.partial_eval` enforces this and errors otherwise. Result gets `.simplified = True`
  and is not re-evaluated for the same lang.
- Every op must know when it is null: `missing(lang)` returns a BOOLEAN expression, never null
  itself.
- `is_op(e, SomeOp)` / `is_expression(e)` are the sanctioned type tests (id-based, works across
  languages) — not `isinstance`.
- Sort order across types (`value_compare`): null is least; booleans < numbers < strings <
  lists < dicts.

## Decisive (null-safe) semantics

JX ops are decisive: null means "out of class", so `add(42, null) = 42`,
`eq(null, null) = true`. The *strict* SQL-level ops live in mo_sqlite and do NOT have these
semantics; the translation from decisive to strict happens in jx_sqlite/mo_sqlite `to_sql`.
Full spec: `C:\Users\kyle\code\ActiveData\docs\jx_decisive_operators.md`.

## This is a transpiler; not every op is a JX op

A **mixed-type column is a valid JX scenario** — JX values are heterogeneous, and JX operators
are defined over that. The hard part is not JX; it is *re-expressing* JX operators in a target
language (Python, C, SQL) whose type systems and operator sets differ. So this codebase carries
**more operators than JX has**: alongside the decisive JX ops there are lower-level primitives
that model the *target* language — e.g. `StrictIndexOfOp`, `StrictEqOp`. Their `Strict*` name
means exactly "decisive/conservative/strict": a host-level operator that assumes its inputs were
already validated and narrowed to the right type.

Consequence: **a strict op is allowed to crash on an out-of-class input** (e.g.
`StrictIndexOfOp.to_python` emits a bare `.find()` that throws on a non-string). That is the
contract, not a bug — do **not** add type guards to strict-op `__call__`/`to_python`. The
decisive→strict lowering is what guarantees valid inputs: a decisive op's `partial_eval` wraps
the strict primitive in the necessary `missing`/type guards (a `WhenOp`, an `IsTextOp`, a schema
`json_type` narrowing) so the strict op only ever runs on values of the type it expects. Fix a
"crash on wrong type" upstream in that lowering, never by softening the strict primitive.

## Open questions (Kyle)

- (query, namespace, language) combination — commits 7aafd1d/37768d8 note the namespace is
  missing from the pipeline. Where should QueryOp acquire its namespace: at parse
  (`jx_expression`), at `QueryOp.wrap`, or at `to_sql`?

- **schema-specific JX as an intermediary (not built, maybe not needed).** High-level JX is
  schema-agnostic: the typed keys are invisible, so a nameless value list `[1, 2, 3]`
  (typed `{"~a~": [{"~i~": 1}, ...]}`) has `nested_path=["."]`. Only `es_column` carries the
  typing (e.g. `.~n~`; see `tests/test_various.py::test_column`). If the schema is known, one
  could split a JX query into schema-specific variants whose nested paths are concrete — the
  same value list would then be `nested_path=["~a~", "."]`. Kyle has **not** built this
  JX → schema-specific-JX → SQL step; it is not used anywhere in this code. Open question
  whether that intermediary is worth introducing, or whether `to_sql` should keep resolving
  schema variation directly.

  Because the Python target is **dynamically typed**, this code deliberately keeps
  `es_column="."` for a nameless primitive list (`[1, 2, 3]`) instead of materializing
  `~i~`/`~s~`/`~a~`: it leans on `to_data`/`from_data`/`enlist`/`delist` (with `isinstance`
  once down at the primitives), so distinguishing integer-vs-string or scalar-vs-array is not
  needed. Consequence: the `Column` constraint must allow a primitive `json_type` at
  `es_column="."` (not only `ARRAY`/`OBJECT`). A strictly-typed destination would instead
  demand `es_column="~i~"` etc., and would split a list/set into per-item schemas with
  (possibly different) operations per record — the schema-specific-JX path above. Kyle notes
  the `es_column="."` choice *may* be wrong long-term, but it is what this code assumes.

- **arrays-of-arrays are out of scope by design.** JX assumes **named properties**; its
  automatic projection over lists is recursive and blind to structure (it is emphatically NOT
  numpy). A bare list-of-lists like `[[1, 2], [3]]` has no elegant representation — the
  operations may not make sense, and schema inference currently errors on it (the inner list
  hits the `json_type=ARRAY → cardinality in [0,1]` constraint; a single-element inner list is
  also unwrapped to a scalar, so a column gets conflicting types). Kyle's stance: an array of
  arrays is really a **tuple** — position carries meaning and should be given **names** — so
  the fix is to name the positions, not to teach JX positional arrays. Left unhandled on
  purpose; do not "fix" `[[...],[...]]` by forcing a nameless-array schema.
