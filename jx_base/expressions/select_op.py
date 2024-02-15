# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from typing import Tuple, Iterable, Dict

from jx_base.expressions._utils import TYPE_CHECK, simplified
from jx_base.expressions.aggregate_op import canonical_aggregates
from jx_base.expressions.default_op import DefaultOp
from jx_base.expressions.expression import jx_expression, Expression, _jx_expression
from jx_base.expressions.leaves_op import LeavesOp
from jx_base.expressions.literal import Literal
from jx_base.expressions.name_op import NameOp
from jx_base.expressions.null_op import NULL
from jx_base.expressions.variable import Variable
from jx_base.language import is_op
from jx_base.models.container import Container
from jx_base.utils import is_variable_name
from mo_dots import *
from mo_future import is_text, text
from mo_imports import export
from mo_json import union_type, value2json
from mo_json.types import JxType
from mo_logs import Log
from mo_math import is_number


class SelectOne:
    def __init__(self, name, value, aggregate=NULL, default=NULL):
        if not isinstance(name, str):
            Log.error("expecting a name")
        _name = object.__new__(Literal)
        _name._value = name
        _name.simplified = True
        self._value = object.__new__(NameOp)
        self._value._name = _name
        if aggregate is not NULL:
            if isinstance(aggregate, str):
                self._value.frum = canonical_aggregates[aggregate](frum=value)
            else:
                self._value.frum = canonical_aggregates[aggregate.__class__](frum=value)
        else:
            self._value.frum = value
        if default is not NULL:
            self._value.frum = DefaultOp(self._value.frum, jx_expression(default))

    def __data__(self):
        return {"name": self.name, "value": self.value, "aggregate": self.aggregate.name}

    @property
    def name(self):
        return self._value._name.value

    @property
    def expr(self):
        return self._value.frum

    @property
    def default(self):
        agg = value = self._value.frum
        if is_op(value, DefaultOp):
            agg = agg.frum
        else:
            return NULL
        if agg.__class__ in canonical_aggregates:
            return value.default

        # without an aggregate, we will treat this as a simple expression, no default
        return NULL

    @property
    def aggregate(self):
        agg = value = self._value.frum
        if is_op(value, DefaultOp):
            agg = agg.frum
        if agg.__class__ in canonical_aggregates:
            return agg
        return NULL

    @property
    def value(self):
        agg = value = self._value.frum
        if is_op(value, DefaultOp):
            agg = agg.frum
        if agg.__class__ in canonical_aggregates:
            return agg.frum
        return value

    @property
    def jx_type(self):
        output = self.value.jx_type
        for step in reversed(split_field(self.name)):
            output = JxType(**{step: output})
        return output

    def set_default(self, default):
        return SelectOne(self.name, DefaultOp(self._value.frum, jx_expression(default)))

    def set_name(self, name):
        return SelectOne(name, self._value.frum)

    def __data__(self):
        return self._value.__data__()

    def __str__(self):
        return str(value2json(self.__data__(), pretty=True))

    __repr__ = __str__


class SelectOp(Expression):
    has_simple_form = True

    def __init__(self, frum, *terms: Tuple[SelectOne], **kwargs: Dict[str, Expression]):
        """
        :param terms: list OF SelectOne DESCRIPTORS
        """
        if TYPE_CHECK and (
            not all(isinstance(term, SelectOne) for term in terms) or any(term.name is None for term in terms)
        ):
            Log.error("expecting list of SelectOne")

        Expression.__init__(self, frum, *[t.value for t in terms], *kwargs.values())
        self.frum = frum
        self.terms = terms + tuple(*(SelectOne(k, v) for k, v in kwargs.items()))
        self._jx_type = union_type(*(t.name + t.value.jx_type for t in terms))

    @classmethod
    def define(cls, expr):
        frum, *selects = to_data(expr).select
        frum = _jx_expression(frum, cls.lang)

        terms = []
        for t in to_data(selects):
            if is_op(t, SelectOp):
                terms.extend(t.terms)
            elif is_text(t):
                if not is_variable_name(t):
                    Log.error("expecting {{value}} a simple dot-delimited path name", value=t)
                terms.append(SelectOne(t, _jx_expression(t, cls.lang)))
            elif t.aggregate:
                # AGGREGATES ARE INSERTED INTO THE CALL CHAIN
                if t.value == None:
                    Log.error("expecting select parameters to have name and value properties")
                options = {k: v for k, v in t.items() if k not in ("name", "value", "aggregate")}
                subfrum = _jx_expression(t.value, cls.lang)
                agg = canonical_aggregates[t.aggregate](subfrum, **options)

                if t.name == None:
                    if is_text(t.value):
                        if not is_variable_name(t.value):
                            Log.error("expecting {{value}} a simple dot-delimited path name", value=t.value)
                        else:
                            terms.append(SelectOne(t.value, agg))
                    else:
                        Log.error("expecting a name property")
                else:
                    terms.append(SelectOne(t.name, agg))
            elif t.name == None:
                if t.value == None:
                    Log.error("expecting select parameters to have name and value properties")
                elif is_text(t.value):
                    if not is_variable_name(t.value):
                        Log.error(
                            "expecting {{value}} a simple dot-delimited path name", value=t.value,
                        )
                    else:
                        terms.append(SelectOne(t.value, _jx_expression(t.value, cls.lang)))
                else:
                    Log.error("expecting a name property")
            else:
                terms.append(SelectOne(t.name, jx_expression(t.value)))
        return SelectOp(frum, *terms)

    # @simplified
    # def partial_eval(self, lang):
    #     frum = self.frum.partial_eval(lang)
    #     new_terms = []
    #     for name, expr in self:
    #         new_expr = expr.partial_eval(lang)
    #         new_terms.append(SelectOne(name, new_expr))
    #
    #     if (
    #         len(new_terms) == 1
    #         and new_terms[0].name == "."
    #         and is_variable(new_terms[0].value)
    #         and new_terms[0].value.var == "row"
    #     ):
    #         return frum
    #     return lang.SelectOp(frum, *new_terms)

    @simplified
    def partial_eval(self, lang):
        new_terms = []
        diff = False
        for term in self.terms:
            name, expr, agg, default = term.name, term.value, term.aggregate, term.default
            new_expr = expr.partial_eval(lang)
            if new_expr is expr:
                new_terms.append(SelectOne(name, expr, agg, default))
                continue
            diff = True

            if expr is NULL:
                return default.partial_eval(lang)
            elif is_op(expr, SelectOp):
                for t in expr.terms:
                    t_name, t_value = t.name, t.value
                    new_terms.append(SelectOne(concat_field(name, t_name), t_value, agg, default))
            else:
                new_terms.append(SelectOne(name, new_expr, agg, default))
                diff = True
        if diff:
            return SelectOp(self.frum, *new_terms)
        else:
            return self

    @property
    def jx_type(self):
        return union_type(*(t.value.jx_type for t in self.terms))

    def apply(self, container: Container):
        result = self.frum.apply(container)
        return SelectOp(result, *self.terms)

    def __iter__(self) -> Iterable[Tuple[str, Expression, str]]:
        """
        :return:  return iterator of (name, value) tuples
        """
        for term in self.terms:
            yield term.name, term.value

    def __data__(self):
        return {"select": [self.frum.__data__()] + [term.__data__() for term in self.terms]}

    def vars(self):
        return set(v for term in self.terms for v in term.value.vars())

    def map(self, map_):
        return SelectOp(self.frum, *(SelectOne(name, value.map(map_)) for name, value in self))


def normalize_one(frum, select, format):
    if is_text(select):
        if select == "*":
            return SelectOp(frum, SelectOne(".", LeavesOp(Variable("."))))
        select = SelectOne(select, jx_expression(select))
    else:
        select = to_data(select)
        unexpected = select.keys() - {
            "name",
            "value",
            "default",
            "aggregate",
            "percentile",
        }
        if unexpected:
            Log.error(
                "Expecting a select clause with `value` property.  Unexpected property: {{unexpected}}",
                unexpected=unexpected,
            )
        if is_missing(select.value) and is_missing(select.aggregate):
            # EXPLICIT REQUEST FOR NOTHING
            return SelectOp(frum)

    name = select.name
    value = select.value
    aggregate = select.aggregate

    if not value:
        canonical = SelectOne(coalesce(name, aggregate), Variable("."), aggregate)
        if not canonical.name and len(select):
            Log.error(BAD_SELECT, select=select)
    elif is_text(value):
        if value == ".":
            canonical = SelectOne(coalesce(name, aggregate, "."), jx_expression(value))
        elif value.endswith(".*"):
            root_name = value[:-2]
            value = jx_expression(root_nam)
            if not is_variable(value):
                Log.error("do not know what to do")
            canonical = SelectOne(coalesce(name, root_name), LeavesOp(value, prefix=select.prefix))
        elif value.endswith("*"):
            root_name = value[:-1]
            path = split_field(root_name)
            expr = jx_expression(root_name)
            if not is_variable(expr):
                Log.error("do not know what to do")
            canonical = SelectOne(
                coalesce(name, aggregate, join_field(path[:-1])),
                LeavesOp(expr, prefix=Literal((select.prefix or "") + path[-1] + ".")),
            )
        else:
            canonical = SelectOne(coalesce(name, value.lstrip("."), aggregate), jx_expression(value))

    elif is_number(value):
        canonical = SelectOne(coalesce(name, str(value)), jx_expression(value))
    else:
        canonical = SelectOne(coalesce(name, value, aggregate), jx_expression(value))

    if aggregate is not NULL and aggregate != None:
        agg_op = canonical_aggregates[aggregate](frum=canonical.value)
        canonical = SelectOne(canonical.name, agg_op)
        if select.percentile:
            if not isinstance(select.pecentile, float):
                Log.error("Expecting `percentile` to be a float")
            agg_op.percentile = select.percentile
    if select.default is not NULL and select.default != None:
        canonical = canonical.set_default(select.default)

    if format != "list" and canonical.name != ".":
        canonical = canonical.set_name(literal_field(canonical.name))

    return SelectOp(Null, canonical)


export("jx_base.expressions.variable", SelectOp)


def _normalize_selects(frum, selects, format) -> SelectOp:
    if len(selects) == 0:
        return SelectOp(frum)
    terms = [ss for s in selects for ss in normalize_one(frum, s, format).terms]

    # ENSURE NAMES ARE UNIQUE
    exists = set()
    for s in terms:
        name = s.name
        if name in exists:
            Log.error("{{name}} has already been defined", name=name)
        exists.add(name)

    return SelectOp(frum, *terms)
