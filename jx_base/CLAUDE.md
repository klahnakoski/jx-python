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
