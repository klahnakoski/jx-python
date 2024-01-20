# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from uuid import uuid4

from jx_base.expressions import jx_expression
from jx_base.expressions.literal import FALSE
from jx_base.expressions.when_op import WhenOp
from jx_base.language import is_op
from jx_base.models.container import Container
from jx_base.models.facts import Facts
from jx_base.models.namespace import Namespace
from jx_base.models.nested_path import NestedPath
from jx_base.models.relation import Relation
from jx_base.models.schema import Schema
from jx_base.models.snowflake import Snowflake
from jx_base.models.table import Table
from jx_base.utils import enlist
from mo_dots import coalesce, to_data, last
from mo_dots.datas import register_data
from mo_future import is_text, text
from mo_imports import expect
from mo_json import (
    value2json,
    true,
    false,
    null,
    _simple_expand,
)
from mo_logs import Log
from mo_logs.strings import quote

Python, Column = expect("Python", "Column")

ENABLE_CONSTRAINTS = True


def generateGuid():
    return text(uuid4())


def _exec(code, name, defines={}):
    try:
        locals = {}
        globs = globals()
        exec(code, {**defines, **globs}, locals)
        temp = locals[name]
        return temp
    except Exception as cause:
        Log.error("Can not make class\n{{code}}", code=code, cause=cause)


_ = last, true, false, null


def _to_python(value):
    return value2json(value)


def failure(row, rownum, rows, constraint):
    constraint = to_data(constraint)
    if constraint["and"]:
        for a in constraint["and"]:
            failure(row, rownum, rows, a)
        return
    expr = jx_expression(constraint)
    try:
        does_pass = expr(row, rownum, row)
    except Exception as cause:
        does_pass = False

    if not does_pass:
        raise Log.error("{{row}} fails to pass {{req}}", row=row, req=expr.__data__())


def DataClass(name, columns, constraint=None):
    """
    Use the DataClass to define a class, but with some extra features:
    1. restrict the data type of property
    2. restrict if `required`, or if `nulls` are allowed
    3. generic constraints on object properties

    It is expected that this class become a real class (or be removed) in the
    long term because it is expensive to use and should only be good for
    verifying program correctness, not user input.

    :param name: Name of the class we are creating
    :param columns: Each columns[i] has properties {
            "name",     - (required) name of the property
            "required", - False if it must be defined (even if None)
            "nulls",    - True if property can be None, or missing
            "default",  - A default value, if none is provided
            "type"      - a Python data type
        }
    :param constraint: a JSON query Expression for extra constraints (return true if all constraints are met)
    :return: The class that has been created
    """
    from jx_python.expression_compiler import compile_expression

    columns = to_data([
        {"name": c, "required": True, "nulls": False, "type": object} if is_text(c) else c for c in columns
    ])
    constraint = {"and": [{"exists": c.name} for c in columns if not c.nulls and c.default == None] + [constraint]}
    slots = columns.name
    required = to_data(filter(lambda c: c.required and c.default == None, columns)).name
    # nulls = to_data(filter(lambda c: c.nulls, columns)).name
    defaults = {c.name: coalesce(c.default, None) for c in columns}
    types = {c.name: coalesce(c.type, object) for c in columns}
    constraint_expr = jx_expression(not ENABLE_CONSTRAINTS or constraint).partial_eval(Python).to_python()
    constraint_func = compile_expression(constraint_expr)

    def _constraint(row0, rownum0, rows0):
        if not ENABLE_CONSTRAINTS:
            return

        def validate(cond):
            expr = jx_expression(cond)
            func = compile_expression(expr.partial_eval(Python).to_python())
            try:
                fvalue = func(row0, rownum0, rows0)
                evalue = expr(row0, rownum0, rows0)
                if fvalue == evalue:
                    return
            except Exception as cause:
                from jx_python.expressions.get_op import get_attr

                fvalue = func(row0, rownum0, rows0)
                evalue = expr(row0, rownum0, rows0)
                Log.error("Can not validate constraint\n{{code}}", code=cond, cause=cause)

            if "and" in cond:
                for i, term in enumerate(cond["and"]):
                    validate(term)
                return
            elif "or" in cond:
                for term in cond["or"]:
                    validate(term)
                return
            elif "not" in cond:
                validate(cond["not"])
                return
            elif "when" in cond:
                validate(cond["when"])
                validate(cond["then"])
                validate(cond["else"])
                return

            fvalue = func(row0, rownum0, rows0)
            evalue = expr(row0, rownum0, rows0)
            Log.error("Can not validate constraint\n{{code}}", code=cond)

        # USE THIS TO DEBUG CONSTRAINTS
        # validate(constraint)

        if constraint_func(row0, rownum0, rows0):
            return
        failure(row0, rownum0, rows0, constraint)
        Log.error(
            "constraint\\n{" + "{code}}\\nnot satisfied {" + "{expect}}\\n{" + "{value|indent}}",
            code=constraint_expr,
            expect=constraint,
            value=row0,
        )

    code = _simple_expand(
        """
import re
from mo_future import is_text, is_binary, Mapping
from mo_dots import Null
from jx_base import failure

meta = None
types_ = {{types}}
defaults_ = {{defaults}}
opener = "{"+"{"

class {{class_name}}(Mapping):
    __slots__ = {{slots}}

    def __init__(self, **kwargs):
        if not kwargs:
            return

        for s in {{slots}}:
            object.__setattr__(self, s, kwargs.get(s, {{defaults}}.get(s, None)))

        missed = {{required}}-set(kwargs.keys())
        if missed:
            Log.error("Expecting properties {"+"{missed}}", missed=missed)

        illegal = set(kwargs.keys())-set({{slots}})
        if illegal:
            Log.error(opener + "names}} are not a valid properties", names=illegal)

        _constraint(self, 0, [self])

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except Exception:
            raise KeyError(item)

    def __setitem__(self, item, value):
        setattr(self, item, value)
        return self

    def __setattr__(self, item, value):
        if item not in {{slots}}:
            Log.error(opener + "item|quote}} not valid attribute", item=item)

        if value==None and item in {{required}}:
            Log.error("Expecting property {"+"{item}}", item=item)

        object.__setattr__(self, item, value)
        _constraint(self, 0, [self])

    def __getattr__(self, item):
        Log.error(opener + "item|quote}} not valid attribute", item=item)

    def __hash__(self):
        return object.__hash__(self)

    def __eq__(self, other):
        try:
            if isinstance(other, {{class_name}}) and dict(self)==dict(other) and self is not other:
                Log.error("expecting to be same object")
            return self is other
        except Exception:
            return False
            
    def __dict__(self):
        return {k: getattr(self, k) for k in {{slots}}}

    def items(self):
        return ((k, getattr(self, k)) for k in {{slots}})

    def __copy__(self):
        _set = object.__setattr__
        output = object.__new__({{class_name}})
        {{assign}}
        return output

    def __iter__(self):
        return {{slots}}.__iter__()

    def __len__(self):
        return {{len_slots}}

    def __str__(self):
        return str({{dict}})

""",
        (
            {
                "class_name": name,
                "slots": "(" + ", ".join(quote(s) for s in slots) + ")",
                "required": "{" + ", ".join(quote(s) for s in required) + "}",
                "defaults": _to_python(defaults),
                "len_slots": len(slots),
                "dict": "{" + ", ".join(quote(s) + ": self." + s for s in slots) + "}",
                "assign": "; ".join("_set(output, " + quote(s) + ", self." + s + ")" for s in slots),
                "types": "{" + ",".join(quote(k) + ": " + v.__name__ for k, v in types.items()) + "}",
                "constraint_expr": constraint_expr.source,
                "constraint": value2json(constraint),
            },
        ),
    )

    output = _exec(code, name, {**constraint_expr.locals, "_constraint": _constraint})
    register_data(output)
    return output
