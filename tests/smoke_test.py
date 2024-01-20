from mo_threads import stop_main_thread

from jx_base import jx_expression
from jx_python.expressions import Python

jx_expression({"add": [1, 2]}).partial_eval(Python).to_python()
stop_main_thread()