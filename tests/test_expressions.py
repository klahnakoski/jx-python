# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
from jx_python.expression_compiler import compile_expression

from mo_testing.fuzzytestcase import FuzzyTestCase, add_error_reporting

from jx_base import jx_expression, NULL
from jx_python.expressions import Python


@add_error_reporting
class TestOther(FuzzyTestCase):
    def test_add(self):
        expr = jx_expression({"add": [1, 2]})

        self.assertEqual(expr(), 3)
        self.assertEqual(expr.partial_eval(Python).to_python().source, "3")

    def test_add2(self):
        expr = jx_expression({"add": [1, 2, 3]})

        self.assertEqual(expr(), 6)
        self.assertEqual(expr.partial_eval(Python).to_python().source, "6")

    def test_subtract(self):
        expr = jx_expression({"subtract": [1, 2]})

        self.assertEqual(expr(), -1)
        self.assertEqual(expr.partial_eval(Python).to_python().source, "-1")

    def test_multiply(self):
        expr = jx_expression({"multiply": [2, 3]})

        self.assertEqual(expr(), 6)
        self.assertEqual(expr.partial_eval(Python).to_python().source, "6")

    def test_divide(self):
        expr = jx_expression({"divide": [6, 2]})

        self.assertEqual(expr(), 3)
        self.assertEqual(expr.partial_eval(Python).to_python().source, "3")

    def test_divide2(self):
        expr = jx_expression({"divide": [6, 0], "default": 1})

        self.assertEqual(expr(), 1)
        self.assertEqual(expr.partial_eval(Python).to_python().source, "1")

    def test_multiply3(self):
        expr = jx_expression({"multiply": [2, 3, 4]})

        self.assertEqual(expr(), 24)
        self.assertEqual(expr.partial_eval(Python).to_python().source, "24")

    def test_multiply4(self):
        expr = jx_expression({"multiply": [2, None, 4]})

        self.assertEqual(expr(), NULL)
        self.assertEqual(expr.partial_eval(Python).to_python().source, "None")

    def test_product(self):
        expr = jx_expression({"product": [2, None, 4]})

        self.assertEqual(expr(), 8)
        self.assertEqual(expr.partial_eval(Python).to_python().source, "8")

    # ------ conservative-vs-decisive null policy (docs/null_semantics.md) ------
    # scalar operators (add, mul, least, most) are CONSERVATIVE: any null ⇒ null.
    # aggregates (sum, product, min, max) are DECISIVE: skip null; null only if all null.
    # the `nulls` clause overrides the default per call.

    def test_add_conservative(self):
        # any null operand ⇒ null
        self.assertEqual(jx_expression({"add": [42, None]})(), NULL)

    def test_add_nulls_override_is_decisive(self):
        # nulls:true flips add to decisive (skip the null)
        self.assertEqual(jx_expression({"add": [42, None], "nulls": True})(), 42)

    def test_sum_decisive(self):
        # aggregate: null skipped
        self.assertEqual(jx_expression({"sum": [42, None]})(), 42)
        # null only when every operand is null
        self.assertEqual(jx_expression({"sum": [None, None]})(), NULL)

    def test_mul_conservative(self):
        self.assertEqual(jx_expression({"mul": [2, None, 4]})(), NULL)

    def test_least_conservative(self):
        # least = conservative minimum (like BigQuery LEAST): any null ⇒ null
        self.assertEqual(jx_expression({"least": [5, 3]})(), 3)
        self.assertEqual(jx_expression({"least": [5, None, 3]})(), NULL)

    def test_most_conservative(self):
        # most = conservative maximum (like BigQuery GREATEST): any null ⇒ null
        self.assertEqual(jx_expression({"most": [5, 3]})(), 5)
        self.assertEqual(jx_expression({"most": [5, None, 3]})(), NULL)

    def test_min_on_fixed_list_decisive(self):
        # min over a fixed-parameter list: decisive, skips null
        self.assertEqual(jx_expression({"min": [5, 3]})(), 3)
        self.assertEqual(jx_expression({"min": [5, None, 3]})(), 3)

    def test_max_on_fixed_list_decisive(self):
        # max over a fixed-parameter list: decisive, skips null
        self.assertEqual(jx_expression({"max": [5, 3]})(), 5)
        self.assertEqual(jx_expression({"max": [5, None, 3]})(), 5)

    def test_and(self):
        value = {"a": False, "b": True, "c": False}
        func = compile_expression(jx_expression({"and": [{"or": ["a", "b"]}, "c"]}).to_python())
        result = func(value)
        self.assertEqual(result, False)

    def test_count(self):
        expr = jx_expression({"count": "nested_path"})
        python = expr.to_python(0)
        self.assertEqual(str(python), 'sum(((0 if v==None else 1) for v in listwrap(get_attr(enlist(row0), "nested_path"))), 0)')

    def test_union(self):
        # union COLLECTS THE DISTINCT VALUES, SKIPPING THE NULLS (DECISIVE)
        expr = jx_expression({"union": "a"})
        row = {"a": ["x", "y", "x", None]}

        self.assertEqual(expr(row), {"x", "y"})
        func = compile_expression(expr.partial_eval(Python).to_python())
        self.assertEqual(func(row), {"x", "y"})

    def test_union_of_one_value(self):
        # A SCALAR COLUMN IS A COLLECTION OF ONE
        expr = jx_expression({"union": "a"})

        self.assertEqual(expr({"a": "x"}), {"x"})
        self.assertEqual(expr({}), set())

    def test_min_of_collection(self):
        # THE AGGREGATES ARE DECISIVE: NULLS ARE SKIPPED, AN EMPTY COLLECTION IS null
        expr = jx_expression({"min": "a"})

        self.assertEqual(expr({"a": [3, 1, None, 2]}), 1)
        self.assertEqual(expr({"a": 3}), 3)
        self.assertEqual(expr({}), NULL)

    def test_max_of_collection(self):
        expr = jx_expression({"max": "a"})

        self.assertEqual(expr({"a": [3, 1, None, 2]}), 3)
        self.assertEqual(expr({"a": 3}), 3)
        self.assertEqual(expr({}), NULL)

    def test_avg_of_collection(self):
        expr = jx_expression({"avg": "a"})

        self.assertEqual(expr({"a": [1, 2, None, 6]}), 3)
        self.assertEqual(expr({"a": 3}), 3)
        self.assertEqual(expr({}), NULL)

    def test_sum_of_one_value(self):
        # A SCALAR COLUMN IS A COLLECTION OF ONE
        expr = jx_expression({"sum": "a"})

        self.assertEqual(expr({"a": [1, 2, None, 6]}), 9)
        self.assertEqual(expr({"a": 3}), 3)
        self.assertEqual(expr({}), 0)

    def test_aggregate_partial_eval_stays_in_language(self):
        # THE AGGREGATES BUILD THEMSELVES IN __new__; IT MUST USE cls SO THE LANGUAGE-SPECIFIC
        # SUBCLASS SURVIVES - A JX OP HANDED BACK TO Python HAS NO to_python
        # avg IS OMITTED: jx_python HAS NO WORKING AvgOp.to_python YET (SEE BUGS.md)
        for op in ["count", "min", "max", "sum", "product"]:
            expr = jx_expression({op: "a"}).partial_eval(Python)
            self.assertIs(expr.lang, Python, f"{op} lost the language")
            expr.to_python(0)
