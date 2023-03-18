from mo_logs import logger

from jx_base import jx_expression
from jx_base.expressions import (
    Expression,
    Variable,
    GetOp,
    EqOp,
    Literal,
    AndOp,
    OrOp,
    NeOp,
    CallOp,
)
from jx_python.expressions import Python, PythonFunction
from jx_python.streams.expression_compiler import compile_expression
from jx_python.streams.inspects import is_function
from jx_python.streams.typers import Typer, JxTyper
from jx_python.streams.typers import UnknownTyper, LazyTyper
from mo_json import JX_ANY

Any = Typer(python_type=JX_ANY)


class ExpressionFactory:
    def __init__(self, expr, codomain):
        self.expr: Expression = expr
        self.codomain: Typer = codomain or LazyTyper()

    def build(self):
        return compile_expression(self.expr.partial_eval(Python).to_python())

    def __getattr__(self, item):
        item_type = getattr(self.codomain, item)
        return ExpressionFactory(GetOp(self.expr, Literal(item)), item_type)

    def __call__(self, *args, **kwargs):
        args = [factory(a).build() for a in args]
        kwargs = {k: factory(v).build() for k, v in kwargs.items()}
        return ExpressionFactory(CallOp(self.expr, *args, **kwargs), JxTyper(JX_ANY))

    def __eq__(self, other):
        other = factory(other)
        return ExpressionFactory(EqOp(self.expr, other.expr), Typer(python_type=bool))

    def __ne__(self, other):
        other = factory(other)
        return ExpressionFactory(NeOp(self.expr, other.expr), Typer(python_type=bool))

    def __and__(self, other):
        other = factory(other)
        return ExpressionFactory(AndOp(self.expr, other.expr), Typer(python_type=bool))

    def __or__(self, other):
        other = factory(other)
        return ExpressionFactory(OrOp(self.expr, other.expr), Typer(python_type=bool))


def factory(expr, codomain=Any) -> ExpressionFactory:
    """
    assemble the expression
    """
    if isinstance(expr, ExpressionFactory):
        return ExpressionFactory(expr.expr, codomain)

    if is_function(expr):
        return ExpressionFactory(PythonFunction(expr), codomain)

    if not isinstance(expr, Expression):
        expr = jx_expression(expr)

    if expr.op == Literal.op:
        return ExpressionFactory(expr, Typer(example=expr.value))

    return ExpressionFactory(expr, codomain)


class TopExpressionFactory(ExpressionFactory):
    """
    it(x)  RETURNS A FunctionFactory FOR x
    """

    def __call__(self, value):
        # much like an import of a value
        if isinstance(value, ExpressionFactory):
            logger.error("don't do this")

        return ExpressionFactory(Literal("."), Typer(python_type=type(value)))

    def __str__(self):
        return "it"


it = TopExpressionFactory(Variable("."), UnknownTyper(Exception("unknonwn type")))
