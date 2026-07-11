# Null semantics: conservative vs decisive operators

Canonical home for this policy (jx_base owns the operator table). Vendored copies in
downstream repos (jx-sqlite, mo-sqlite) arrive via svn sync.

JX has two null policies for multi-operand math/comparison operators. Which one an operator
uses **by default** is fixed by the operator's name; the `nulls` clause overrides it per call.

## The rule

- **Scalar / fixed-arity operators are CONSERVATIVE by default** — if *any* operand is null
  (missing / out-of-class), the result is null. Null is contagious.
- **Aggregates are DECISIVE by default** — null operands are *skipped*; the result is null
  only when *every* operand is null.

| operation | conservative (scalar) | decisive (aggregate) |
|-----------|-----------------------|----------------------|
| add       | `add`                 | `sum`                |
| multiply  | `mul` / `mult` / `multiply` | `product`       |
| minimum   | `least`               | `min`                |
| maximum   | `most`                | `max`                |

Examples (default behavior):

    {"add":      [42, null]}      => null     {"sum":     [42, null]}      => 42
    {"multiply": [2, null, 4]}    => null     {"product": [2, null, 4]}    => 8
    {"least":    [5, null, 3]}    => null     {"min":     [5, null, 3]}    => 3
    {"most":     [5, null, 3]}    => null     {"max":     [5, null, 3]}    => 5

`min` / `max` accept a **fixed-parameter list** (decisive), in addition to their aggregate
form over a collection. Internally `{"min": [...]}` is `LeastOp(..., nulls=True)` and
`{"max": [...]}` is `MostOp(..., nulls=True)` — the decisive twins of `least` / `most`.

## Overriding with `nulls`

Every scalar op accepts a `nulls` clause that flips the default for that call:

    {"add":     ["a", "b"], "nulls": true}   # decisive add:  add(0, missing) => 0
    {"least":   ["a", "b"], "nulls": true}   # decisive least: skips missing

Pairs with `default`: when a conservative op yields null, a `default` clause supplies the
fallback — `{"add": ["a","b"], "default": -5}` gives -5 whenever `a` or `b` is missing.

## Why this split (SQL / BigQuery / Athena)

Every SQL dialect already draws this line the same way, and the names above mirror it:

- Scalar arithmetic `a + b`, `a * b` → **NULL propagates** (conservative). → `add`, `mul`.
- Aggregates `SUM(col)`, `MIN(col)`, `MAX(col)` → **ignore NULL rows** (decisive). →
  `sum`, `product`, `min`, `max`.
- BigQuery / Athena fixed-arity scalars `LEAST(...)` / `GREATEST(...)` → **NULL if any arg
  is NULL** (conservative). → `least`, `most`.

So: the operator you'd write inline in a row expression is conservative; the function you'd
apply across a collection is decisive. Same operation, two names, chosen by which null policy
you want.

## Implementation notes

Operator table: `jx_base/expressions/__init__.py`. `BaseMultiOp` carries `decisive` (set from
the `nulls` clause, default `False` = conservative); `missing()` is `AND` of operand-missing
when decisive, `OR` when conservative. `add`/`mul`/`least`/`most` are `BaseMultiOp` subclasses;
`sum`/`product` are the decisive aggregate forms; `min`/`max` (`MinOp`/`MaxOp`) delegate a
fixed-parameter list to `LeastOp`/`MostOp` with `nulls=True`.

Resolved 2026-07-11: `LeastOp.partial_eval` no longer skips a null operand when conservative
(it now returns null); `"min"` is registered in the operator table (was missing, so
`{"min": [...]}` errored). Remaining gap: passing an explicit `nulls` clause to the aggregate
forms (`sum`/`product`/`min`/`max`) currently errors rather than overriding — decide whether
that override is meaningful for aggregates.
