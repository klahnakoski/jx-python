# jx_python — JX interpreted over Python objects

The **Python** language (`expressions/__init__.py: Python.register_ops(vars())`): the same JX
operators as jx_base, but compiled to Python source (`expression_compiler.py`) and run over
in-memory lists/Data.

Role in this repo:

- **Just another language mapping** — as buggy as the others. It is NOT a reference
  implementation; do not treat a jx_python result as ground truth when it disagrees with
  sqlite. Ground truth is the expected values written in the tests (and the decisive-operator
  spec).
- **Post-processing shortcuts** — some query stages are finished in Python rather than SQL as
  a shortcut to get a result (window functions in `windows.py`, grouping in `group_by.py`,
  containers in `containers/`), not because SQL fundamentally can't express them.
- `namespace/normal.py` normalizes raw query JSON into canonical `QueryOp` form ("normal
  form") — relevant to the open (query, namespace, language) design question.
