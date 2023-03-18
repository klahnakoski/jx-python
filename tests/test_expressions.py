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
        self.assertEqual(expr.partial_eval(Python).to_python().source, "3.0")
