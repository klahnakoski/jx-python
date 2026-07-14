# test_jx — shared JX conformance suite

This directory is a **backend-agnostic conformance suite**: every test is a data-driven case of
the form `{data, query, expecting_*}`. It is checked out from SVN (`^/tests/test_jx` in the
`pyLibrary` repo) into each repo that implements JX, so the *same* tests exercise jx_python
(in-memory), jx_sqlite (SQL), the ES/http service, etc. Edit the tests here and commit them
back to SVN so every consumer gets the change (see the repo root `CLAUDE.md` for the git↔SVN
sync). **Do not fork per-repo copies** — a bug found by one backend is a case all backends
should pass.

## How a test runs

`__init__.py` here defines `BaseTestCase(FuzzyTestCase)`. It does **not** know how to execute a
query. Instead it reads two module globals that the *consuming repo* must set:

- `test_jx.global_settings` — parsed config (must contain `use`, e.g. `"python"`, `"sqlite"`).
- `test_jx.utils` — the **harness**: an object that knows how to load data and run queries
  against this repo's backend.

`BaseTestCase.__init__` errors out if `utils` is still `None`, pointing at `./tests/__init__.py`.
So each repo supplies the harness by importing this package and assigning those globals from its
own `tests/__init__.py`. (This module-global injection is deliberate and shared with jx_sqlite;
it is the unittest-native seam here — there is no pytest fixture. Keep it.)

A typical test body is just:

```python
from tests.test_jx import BaseTestCase, TEST_TABLE

class TestX(BaseTestCase):
    def test_thing(self):
        self.utils.execute_tests({
            "data": [{"a": 1}],
            "query": {"from": TEST_TABLE, "select": "a"},
            "expecting_list": {"meta": {"format": "list"}, "data": [1]},
        })
```

`TEST_TABLE == "testdata"`; queries name their source as `TEST_TABLE` (or a nested path under
it like `"testdata.a"`). The harness is responsible for pointing that name at real data.

## Writing a harness (`<repo>/tests/__init__.py`)

Create a `utils` class implementing the interface `BaseTestCase` and the tests call, then set the
globals at import time. Minimum surface actually used by the suite:

| method | contract |
| --- | --- |
| `setUp` / `tearDown` | per-test lifecycle (fresh container, close db, …) |
| `setUpClass` / `tearDownClass` | per-class lifecycle; called from `BaseTestCase` |
| `execute_tests(subtest, tjson=False, places=6)` | the main entry: load `subtest.data`, then run every `expecting_*` clause and compare |
| `fill_container(subtest, typed=False)` | load `subtest.data` into the backend under `TEST_TABLE`; also used directly by a few tests |
| `execute_query(query)` | run one query dict, return a result whose `.meta.format` is `list`/`table`/`cube` |
| `execute_update(command)` | apply a `{set,clear,where}` update (only `test_update.py`) |
| `try_till_response(...)` | http-service shim; only the ES/service tests call it — safe to stub/raise otherwise |

`execute_tests` should mirror the reference harnesses: for each key on the subtest,
`expecting_<fmt>` selects the requested format (`expecting` = default format), it sets
`query.format` and `query.meta.testing = True`, runs the query, and compares. `expecting_error`
means the query *should* raise, and the expected string must appear in the raised cause.

The comparison is format-aware and order-insensitive unless the query has an explicit `sort`
(the reference `compare_to_expected` sorts both sides first). Reuse that logic rather than
reimplementing it: in jx_python it lives as methods on `JxTestHarness` (`compare_to_expected`
plus the `sort_table` / `cube2list` / `list2cube` staticmethods), so a second backend just
subclasses and inherits them. They are backend-neutral (they only use `jx.sort`,
`jx.get_columns`, `assertAlmostEqual`, and `QueryOp.wrap(query, container_or_Null, self.lang)`).

### Two reference implementations

- **jx_python** — `jx-python/tests/__init__.py`, class `JxTestHarness`. All the generic
  machinery is on the class; the backend seam is just `make_container` + `execute_query`
  (override those to add another jx_python execution mode, e.g. interpreted over Data/FlatList;
  set the `lang` class attr if the language differs). The default builds a
  `ListContainer(name=".", data=...)`, substitutes that container object into `query["from"]`
  (replacing the `TEST_TABLE` string), normalizes with `QueryOp.wrap(query, container, self.lang)`,
  and runs `container.query(query_op)` (which honors `format`). Config: `tests/config/python.json`
  (`"use": "python"`). Note `name="."`, **not** `"testdata"` — a container named `testdata`
  makes the schema treat it as a nested-path prefix and violates a `Column` constraint.
- **jx_sqlite** — `jx-sqlite/tests/__init__.py`, class `SQLiteUtils`. Inserts into a
  `mo_sqlite` `Facts` table, rewrites `TEST_TABLE` → the real table name, and runs
  `table.query(query)`. Config: `tests/config/sqlite.json`.

### Config

`__init__.py` reads `tests/config/<backend>.json` (override with the `TEST_CONFIG` env var). It
must set `use`; add backend-specific keys (e.g. `db` for sqlite) as needed. `use` also drives the
`@skipIf(global_settings.use == "sqlite", ...)` guards on tests — many modules (`test_others`,
parts of `test_metadata`) target the ES/http endpoint and are expected to skip or fail on
in-process backends. That's normal; measure a backend against the subset meant for it.

## Backends are not reference implementations

A failing test here means this backend disagrees with the *written expected value*, which is the
ground truth — not that another backend is right. jx_python especially is "as buggy as the
others" (see `jx_python/CLAUDE.md`); e.g. the current in-memory harness surfaces a real
`jx.sort(..., already_normalized=True)` signature bug that fails every sorted query. Track real
defects in `jx_python/BUGS.md`, not by weakening the tests.
