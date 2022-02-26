# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import absolute_import, division, unicode_literals

import operator

from jx_base.language import is_expression, Language
from mo_dots import is_sequence, is_missing
from mo_future import (
    get_function_name,
    is_text,
    items as items_,
    text,
    utf8_json_encoder,
)
from mo_imports import expect
from mo_json import BOOLEAN, INTEGER, IS_NULL, NUMBER, STRING, scrub
from mo_json.types import union_type, to_json_type
from mo_logs import Except, Log
from mo_math import is_number
from mo_times import Date

TYPE_CHECK = True  # A LITTLE FASTER IF False
ALLOW_SCRIPTING = False
EMPTY_DICT = {}

Literal, TRUE, FALSE, NULL, TupleOp, Variable = expect(
    "Literal", "TRUE", "FALSE", "NULL", "TupleOp", "Variable"
)


def extend(cls):
    """
    DECORATOR TO ADD METHODS TO CLASSES
    :param cls: THE CLASS TO ADD THE METHOD TO
    :return:
    """

    def extender(func):
        setattr(cls, get_function_name(func), func)
        return func

    return extender


def simplified(func):
    def mark_as_simple(self, lang):
        if self.simplified:
            return self

        output = func(self, lang)
        output.simplified = True
        return output

    func_name = get_function_name(func)
    mark_as_simple.__name__ = func_name
    return mark_as_simple


def jx_expression(expr, schema=None):
    if expr == None:
        return None

    # UPDATE THE VARIABLE WITH THEIR KNOWN TYPES
    output = _jx_expression(expr, language)
    if not schema:
        return output
    return output.to_jx(schema).partial_eval(language)


def _jx_expression(expr, lang):
    """
    WRAP A JSON EXPRESSION WITH OBJECT REPRESENTATION
    """
    if is_expression(expr):
        # CONVERT TO lang
        new_op = expr
        if not new_op:
            # CAN NOT BE FOUND, TRY SOME PARTIAL EVAL
            return language[expr.get_id()].partial_eval(lang)
        return expr
        # return new_op(expr.args)  # THIS CAN BE DONE, BUT IT NEEDS MORE CODING, AND I WOULD EXPECT IT TO BE SLOW

    if expr is True:
        return TRUE
    elif expr is False:
        return FALSE
    elif is_missing(expr):
        return NULL
    elif is_text(expr):
        return Variable(expr)
    elif is_number(expr):
        return Literal(expr)
    elif expr.__class__ is Date:
        return Literal(expr.unix)
    elif is_sequence(expr):
        return TupleOp([_jx_expression(e, lang) for e in expr])

    # expr = to_data(expr)
    try:
        items = items_(expr)

        for op, term in items:
            # ONE OF THESE IS THE OPERATOR
            full_op = operators.get(op)
            if full_op:
                class_ = lang.ops[full_op.get_id()]
                if class_:
                    return class_.define(expr)

                # THIS LANGUAGE DOES NOT SUPPORT THIS OPERATOR, GOTO BASE LANGUAGE AND GET THE MACRO
                class_ = language[op.get_id()]
                output = class_.define(expr).partial_eval(lang)
                return _jx_expression(output, lang)
        else:
            if not items:
                return NULL
            raise Log.error("{{instruction|json}} is not known", instruction=expr)

    except Exception as cause:
        Log.error("programmer error expr = {{value|quote}}", value=expr, cause=cause)


language = Language(None)


_json_encoder = utf8_json_encoder


def value2json(value):
    try:
        scrubbed = scrub(value, scrub_number=float)
        return text(_json_encoder(scrubbed))
    except Exception as e:
        e = Except.wrap(e)
        Log.warning("problem serializing {{type}}", type=text(repr(value)), cause=e)
        raise e


def merge_types(jx_types):
    """
    :param jx_types: ITERABLE OF jx TYPES
    :return: ONE TYPE TO RULE THEM ALL
    """
    return union_type(*(to_json_type(t) for t in jx_types))


_merge_score = {IS_NULL: 0, BOOLEAN: 1, INTEGER: 2, NUMBER: 3, STRING: 4}
_merge_types = {v: k for k, v in _merge_score.items()}

builtin_ops = {
    "ne": operator.ne,
    "eq": operator.eq,
    "gte": operator.ge,
    "gt": operator.gt,
    "lte": operator.le,
    "lt": operator.lt,
    "add": operator.add,
    "sub": operator.sub,
    "mul": operator.mul,
    "max": lambda *v: max(v),
    "min": lambda *v: min(v),
}

operators = {}
