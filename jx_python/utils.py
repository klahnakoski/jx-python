# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import itertools


def distinct(values):
    acc = set()
    result = []
    for v in values:
        if v in acc:
            continue
        acc.add(v)
        result.append(v)
    return result


def group(values, func):
    yield from itertools.groupby(sorted(values, key=func), func)


def wrap_function(func):
    """
    RETURN A THREE-PARAMETER WINDOW FUNCTION TO MATCH
    """
    numarg = func.__code__.co_argcount
    if numarg == 0:

        def temp(row, rownum=None, rows=None):
            return func()

        return temp
    elif numarg == 1:

        def temp(row, rownum=None, rows=None):
            return func(row)

        return temp
    elif numarg == 2:

        def temp(row, rownum=None, rows=None):
            return func(row, rownum)

        return temp
    elif numarg == 3:
        return func


def merge_locals(*locals, **kwargs):
    """
    return the merge of tuples-of-dicts, dicts and kwargs
    """
    output = {}
    for l in locals:
        if isinstance(l, dict):
            output.update(l)
        else:
            for ll in l:
                output.update(ll)
    output.update(kwargs)
    return output
