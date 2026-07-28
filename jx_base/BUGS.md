# jx_base — known defects

All below are FIXED in the jx-sqlite vendored copy but still owe upstream tests (add the
listed coverage, then upstream via svn-sync or the next lib-sync reverts the fix).

## 1. `is_expression` fooled by FlatList
`language.py is_expression` tested `getattr(call, ID, None) != None`; a `FlatList` broadcasts
attribute access (returns a FlatList of Nulls) so any non-empty FlatList passed as an
expression (e.g. `{"eq": ["a", [{"literal":"4"},{"literal":"2"}]]}` crashed in partial_eval).
Fix: check `isinstance(getattr(call, ID, None), int)`.
Coverage: `is_expression` over FlatList / list / Data / op instance / op class; `{"eq":[field,
[literal,literal]]}` and the `in` form produce working expressions.

## 2. `query_metadata` used the old 1-arg `QueryOp.wrap`
`meta_columns.py query_metadata` called `QueryOp.wrap(query)`; signature is now
`wrap(query, container, lang)`. Fix: pass the denormalized columns ListContainer and `JX`.
Coverage: `test_metadata.test_meta` (meta.columns in all three formats).

## 3. `sort_op._normalize_sort` rejects Data-wrapped sort items
A sort item arriving as `Data('.')` fell past the `is_text` branch. Fix: `s = from_data(s)` at
the top of the loop.
Coverage: `_normalize_sort` over Data-wrapped fieldname, plain fieldname, list,
`{field: direction}`, `{"field":…, "sort":…}`.

## 4. `"mult"`/`"mul"`/`"multiply"` mapped to ProductOp (forced decisive; `nulls` crashes)
ProductOp is always decisive and rejects a `nulls` clause — asymmetric with `"add"→AddOp`.
Fix: `"mul"/"mult"/"multiply"→MulOp`; `"product"` stays ProductOp.
Coverage: `{"mult":["a","b"]}` over a missing operand (expect null); `{"mult":[...],"nulls":true}`
(expect decisive, no crash).

## 5. Bare-string select never reached `.*`/`*` handling; `.*` had a NameError; `is_variable` unimported
`select_op.normalize_one` eagerly parsed a bare-string select to a GetOp before the
`is_text(value)` wildcard branches, so `select:["a.*"]`/`["a*"]` returned all nulls; the `.*`
branch also had `root_nam` (typo) and used unimported `is_variable`. Fix: keep raw text as
`{"value": select}` so it flows through the wildcard branches; `root_nam`→`root_name`; import
`is_variable`. (jx_sqlite select_op LeavesOp branch honors `prefix` so `a*`→literal dotted keys.)
Coverage: `normalize_one` over `"a.*"`, `"a*"`, `"*"`, plain `"a"`.

## 6. `CaseOp.partial_eval` leaks a bare then into `whens`; inner-else duplicated per inner when
(a) A `when` folding TRUE did `whens.append(w.then...)` — a bare value where consumers expect
WhenOps. Fix: the folded then becomes `_else` and the loop breaks (a TRUE when is the else for
whens so far). (b) Flattening a nested CaseOp then-clause appended the inner else inside the
inner-when loop (duplicated/shadowing). Fix: move it after the loop; pass `then=` not positional.
Trigger: any `between` (its partial_eval builds such CaseOps).
Coverage: CaseOp with a when folding TRUE mid-sequence; nested CaseOp as then-clause with an else.
