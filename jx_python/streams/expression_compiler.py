# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import, division

from mo_dots import Data, is_data, leaves_to_data
from mo_future import first
from mo_imports import export
from mo_logs import Log, strings
from mo_times.dates import Date

from jx_base.expressions.python_script import PythonScript

GLOBALS = {
    "Date": Date,
    "Log": Log,
    "Data": Data,
    "leaves_to_data": leaves_to_data,
    "is_data": is_data,
    "first": first,
}


def compile_expression(code: PythonScript, function_name="output"):
    """
    THIS FUNCTION IS ON ITS OWN FOR MINIMAL GLOBAL NAMESPACE

    :param code:  PYTHON SOURCE CODE
    :param function_name:  OPTIONAL NAME TO GIVE TO OUTPUT FUNCTION
    :return:  PYTHON FUNCTION
    """

    fake_globals = {**GLOBALS, **code.locals}
    fake_locals = {}
    loop_depth = 0
    try:
        exec(
            (
                "def "
                + function_name
                + f"(row{loop_depth}, rownum{loop_depth}=None, rows{loop_depth}=None):\n"
                + "    _source = "
                + strings.quote(code.source)
                + "\n"
                + "    try:\n"
                + "        return "
                + code.source
                + "\n"
                + "    except Exception as e:\n"
                + "        Log.error('Problem with dynamic function {{func|quote}}', "
                " func=_source, cause=e)\n"
            ),
            fake_globals,
            fake_locals,
        )
        func = fake_locals[function_name]
        setattr(func, "_source", code.source)
        return func
    except Exception as e:
        raise Log.error("Bad source: {{source}}", source=code.source, cause=e)


export("jx_python.expressions._utils", compile_expression)
