# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#

from __future__ import absolute_import, division, unicode_literals

from mo_testing.fuzzytestcase import FuzzyTestCase

from jx_base import jx_expression
from jx_python.expressions import Python


class TestOther(FuzzyTestCase):

    def test_add(self):
        from jx_python import jx

        expr = jx_expression({"add": [1, 2]})

        self.assertEqual(expr(), 3)
        self.assertEqual(expr.partial_eval(Python).to_python(), "3.0")