from jx_base import jx_expression
from jx_python.expressions import Python

jx_expression({"add": [1, 2]}).partial_eval(Python).to_python()
