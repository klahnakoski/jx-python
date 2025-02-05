# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#


import re

from mo_dots import is_list, is_many, is_data
from mo_json.typed_object import TypedObject

from mo_logs import Log

from mo_json import ARRAY_KEY

keyword_pattern = re.compile(r"(\w|[\\.])(\w|[\\.$-])*(?:\.(\w|[\\.$-])+)*")
UID = "__id__"
GUID = "_id"


def is_variable_name(value):
    if value.__class__.__name__ == "Variable":
        Log.warning("not expected")
        return True

    if not value or not str(value):
        return False  # _a._b
    value = value.lstrip(".")
    if not value:
        return True
    match = keyword_pattern.match(value)
    if not match:
        return False
    return match.group(0) == value


def dequote(s):
    """
    If a string has single or double quotes around it, remove them.
    Make sure the pair of quotes match.
    If a matching pair of quotes is not found, return the string unchanged.
    """
    if (s[0] == s[-1]) and s.startswith(("'", '"')):
        return s[1:-1]
    return s


def is_column_name(col):
    if re.match(r"(\$|\w|\\\.)+(?:\.(\$|\w|\\\.)+)*\.\$\w{6}$", col):
        return True
    else:
        return False


def get_property_name(s):
    if s == ".":
        return s
    else:
        return s.lstrip(".")


def coalesce(*args):
    # pick the first not null value
    # http://en.wikipedia.org/wiki/Null_coalescing_operator
    for a in args:
        if a != None:
            return a
    return None


def enlist(value):
    if value == None:
        return []
    if isinstance(value, TypedObject):
        if value[ARRAY_KEY] is not None:
            return value
        return TypedObject([value._boxed_value], **value._attachments)
    elif is_list(value):
        return value
    elif is_many(value):
        return list(value)
    elif is_data(value) and ARRAY_KEY in value:
        return TypedObject(value[ARRAY_KEY], **{k: v for k, v in value.items() if k != ARRAY_KEY})
    else:
        return [value]


def delist(values):
    if isinstance(values, TypedObject):
        return delist(values._boxed_value)
    elif not is_many(values):
        return values
    elif len(values) == 0:
        return None
    elif len(values) == 1:
        return values[0]
    elif is_data(values) and ARRAY_KEY in values:
        return delist(values[ARRAY_KEY])
    else:
        return values
