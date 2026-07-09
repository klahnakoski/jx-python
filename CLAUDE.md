# jx-python

JX query expressions interpreted over in-memory Python objects. The two main packages are
`jx_base` (the abstract JX language — see `jx_base/CLAUDE.md`) and `jx_python` (the Python
mapping — see `jx_python/CLAUDE.md`). Known defects are tracked in `jx_python/BUGS.md`.

## Dependencies come from two places

- **`vendor/`** — svn-synced source copies of several `mo_*` libraries (mo_logs, mo_json,
  mo_future, mo_imports, mo_testing, mo_times, ...). With `vendor/` on `PYTHONPATH`, these
  **override** any pip-installed copy of the same package. This is why the run command below
  puts `vendor` on the path. **Editing vendored code is allowed** — each `vendor/*` is an SVN
  working copy, and its changes are synced back to that package's canonical repo eventually
  (via `svn-sync`). So a fix in `vendor/mo_json` is a real fix to `mo_json`, not a throwaway.
- **pip (`.venv`)** — everything not vendored (mo_dots, mo_sql, mo_collections, mo_kwargs,
  mo_json_config, mo_threads, dateutil, ...) comes from the virtualenv.

`jx_base/` and `jx_python/` are the project's own source (not vendored); edit them directly.

## Setup

Use the repo's `.venv`. Install requirements in this order:

```bash
.venv/Scripts/python.exe -m pip install -r tests/requirements.txt
.venv/Scripts/python.exe -m pip install -r packaging/requirements.txt
```

## Running tests

**Always run from the repo root**, with `.venv`'s interpreter and `PYTHONPATH=.;vendor`.

```bash
# bash / git-bash
PYTHONPATH=".;vendor" .venv/Scripts/python.exe -m unittest discover . -v

# one module / one test
PYTHONPATH=".;vendor" .venv/Scripts/python.exe -m unittest tests.test_sort -v
```

```powershell
# PowerShell
$env:PYTHONPATH = ".;vendor"; .\.venv\Scripts\python.exe -m unittest discover . -v
```

`PYTHONPATH=.;vendor` matters: `.` puts the project packages first, `vendor` supplies the
overriding `mo_*` sources. Omitting `vendor` picks up stale pip copies and fails on imports
(e.g. `cannot import name 'KEY' from 'mo_dots'`). CI runs the equivalent via
`.github/workflows/build.yml` (`pip install .` then `python -m unittest discover . -v`).

## Git ↔ SVN sync

This repo is mirrored into Subversion in addition to git: there is an `svn` git branch that
tracks what is committed to SVN, and `jx_base/`, `jx_python/`, and each `vendor/*` are SVN
working copies (`.svn` is git-ignored). Sync is driven by the user-global `svn-sync` skill.
Fixes to vendored code and to `jx_base`/`jx_python` must reach the SVN source or the next sync
reverts them (see `jx_python/BUGS.md`).
