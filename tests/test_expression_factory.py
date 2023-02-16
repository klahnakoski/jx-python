# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import os
from unittest import TestCase

from jx_python.streams import stream

IS_TRAVIS = bool(os.environ.get("TRAVIS"))


class TestExpressionFactory(TestCase):
    def test_deep_iteration(self):
        class Something:
            def __init__(self, value):
                self.value = value

        value = Something({"props": [{"a": 1}, {"a": 2}, {"a": 3}]})
        result = stream(value).value.props.a.to_list()
        self.assertEqual(result, [1, 2, 3])
