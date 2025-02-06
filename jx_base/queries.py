# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#


import re


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
