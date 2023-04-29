# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#


from mo_testing.fuzzytestcase import FuzzyTestCase
from mo_threads import stop_main_thread

from jx_base import jx_expression
from jx_python.expressions import Python


class TestOther(FuzzyTestCase):
    @classmethod
    def tearDownClass(cls):
        stop_main_thread()

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

