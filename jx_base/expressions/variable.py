# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.expressions.expression import Expression, Literal
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.get_op import GetOp
from jx_base.expressions.null_op import NULL
from jx_base.language import is_op
from mo_dots import join_field
from jx_base.utils import get_property_name
from mo_dots import is_sequence, split_field, startswith_field, concat_field
from mo_dots.lists import last
from mo_future import is_text
from mo_imports import expect, export
from mo_json.typed_encoder import inserter_type_to_json_type
from mo_json.types import to_jx_type, JxType
from mo_logs import Log

QueryOp, SelectOp = expect("QueryOp", "SelectOp")


class Variable(Expression):
    def __init__(self, var, type=None):
        """
        :param var:   DOT DELIMITED PATH INTO A DOCUMENT
        :param type:  JSON TYPE, or JX TYPE, IF KNOWN
        """
        Expression.__init__(self, None)

        self.var = get_property_name(var)

        if type == None:
            # MAYBE THE NAME HAS A HINT TO THE TYPE
            self._data_type = to_jx_type(inserter_type_to_json_type.get(last(split_field(var))))
        else:
            self._data_type = to_jx_type(type)
        if not isinstance(self._data_type, JxType):
            Log.error("expecting JX type")

    def __call__(self, row, rownum=None, rows=None):
        path = split_field(self.var)
        for step in path:
            try:
                row = getattr(row, step)
            except Exception:
                try:
                    row = row[step]
                except Exception:
                    return None
        if is_sequence(row) and len(row) == 1:
            return row[0]
        return row

    def __data__(self):
        return self.var

    def partial_eval(self, lang):
        path = split_field(self.var)
        if len(path) == 1 and path[0] in ["row", "rownum", "rows"]:
            return lang.Variable(self.var)

        base = lang.Variable("row")
        if not path:
            return base
        elif path[0] == "row":
            path = path[1:]
        elif path[0] == "rownum":
            # MAGIC VARIABLES
            base = lang.Variable("rownum")
            path = path[1:]
        elif path[0] == "rows":
            base = lang.Variable("rows")
            path = path[1:]
            if len(path) == 0:
                return base
            elif path[0] in ["first", "last"]:
                base = "rows." + path[0] + "()"
                path = path[1:]
            else:
                Log.error("do not know what {{var}} of `rows` is", var=path[1])

        return lang.GetOp(base, *(Literal(p) for p in path))

    def vars(self):
        return {self.var}

    def map(self, map_):
        replacement = map_.get(self.var)
        if replacement is None:
            return self
        if is_text(replacement):
            return Variable(replacement)
        else:
            return replacement

    def to_jx(self, schema):
        paths = {}
        for rel_name, leaf in schema.leaves(self.var):
            paths.setdefault(leaf.nested_path[0], []).append((rel_name, leaf))

        if len(paths) == 1:
            columns = paths.get(schema.nested_path[0])
            if columns and len(columns) == 1 and columns[0][1].es_column == self.var:
                return self

        selects = []
        for path, leaves in paths.items():
            if startswith_field(path, schema.nested_path[0]) and len(path) > len(schema.nested_path[0]):
                selects.append({
                    "name": self.var,
                    "value": QueryOp(
                        frum=schema.container.get_table(path),
                        select=SelectOp(
                            schema,
                            (
                                {
                                    "name": rel_name,
                                    "value": Variable(leaf.es_column, leaf.json_type),
                                    "aggregate": NULL,
                                }
                                for rel_name, leaf in leaves
                            ),
                        ),
                    ),
                    "aggregate": NULL,
                })
            else:
                selects.extend(
                    {
                        "name": concat_field(self.var, rel_name),
                        "value": Variable(leaf.es_column, leaf.json_type),
                        "aggregate": NULL,
                    }
                    for rel_name, leaf in leaves
                )

        return self

    def __hash__(self):
        return self.var.__hash__()

    def __eq__(self, other):
        if is_op(other, Variable):
            return self.var == other.var
        elif is_text(other):
            return self.var == other
        return False

    def __unicode__(self):
        return self.var

    def __str__(self):
        return str(self.var)

    def missing(self, lang):
        if self.var == "_id":
            return FALSE
        else:
            return lang.MissingOp(self)


def get_variable(expr):
    """
    ATTEMPT TO SIMPLIFY EXPRESSION TO A VARIABLE
    """
    if is_op(expr, Variable):
        return expr
    elif is_text(expr):
        return Variable(expr)
    elif is_op(expr, GetOp) and is_op(expr.frum, Variable) and expr.frum.var=="row" and all(is_op(o, Literal) for o in expr.offsets):
        return Variable(join_field(o.value for o in expr.offsets))
    else:
        expr


IDENTITY = Variable(".")

export("jx_base.expressions._utils", Variable)
export("jx_base.expressions.expression", Variable)
export("jx_base.expressions.base_binary_op", Variable)
export("jx_base.expressions.basic_in_op", Variable)
export("jx_base.expressions.from_op", Variable)
