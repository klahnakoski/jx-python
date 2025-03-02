# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import re

from mo_dots import Data, coalesce, is_data, leaves_to_data, listwrap
from mo_future import first
from mo_logs import Log, strings
from mo_times.dates import Date


def get_attr(value, item):
    try:
        return listwrap(getattr(value, item))
    except:
        pass

    return listwrap(value[item])


GLOBALS = {
    "true": True,
    "false": False,
    "null": None,
    "EMPTY_DICT": {},
    "coalesce": coalesce,
    "listwrap": listwrap,
    "Date": Date,
    "Log": Log,
    "Data": Data,
    "re": re,
    "leaves_to_data": leaves_to_data,
    "is_data": is_data,
    "first": first,
    "get_attr": get_attr,
}


def compile_expression(source, function_name="output"):
    """
    THIS FUNCTION IS ON ITS OWN FOR MINIMAL GLOBAL NAMESPACE

    :param source:  PYTHON SOURCE CODE
    :param function_name:  OPTIONAL NAME TO GIVE TO OUTPUT FUNCTION
    :return:  PYTHON FUNCTION
    """

    locals = {}
    try:
        exec(
            (strings.outdent(
                f"""
                def {function_name}(row0, rownum0=None, rows0=None):
                    _source = {strings.quote(source)}
                    try:
                        return {source}
                    except Exception as e:
                        Log.error('Problem with dynamic function {{func|quote}}', func=_source, cause=e)
                """
            )),
            {**GLOBALS, **source.locals},
            locals,
        )
        func = locals[function_name]
        setattr(func, "_source", source)
        return func
    except Exception as e:
        raise Log.error("Bad source: {source}", source=source, cause=e)
