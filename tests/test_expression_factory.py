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
from jx_python.streams.expression_factory import it

IS_TRAVIS = bool(os.environ.get("TRAVIS"))


class TestExpressionFactory(TestCase):
    def test_deep_iteration(self):
        class Something:
            def __init__(self, value):
                self.value = value

        value = Something({"props": [{"a": 1}, {"a": 2}, {"a": 3}]})
        result = stream(value).value.props.a.to_list()
        self.assertEqual(result, [1, 2, 3])

    def test_iterator(self):
        class Something:
            def __init__(self, value):
                self.value = value

        value = Something({"props": [{"a": 1}, {"a": 2}, {"a": 3}]})
        result = list(stream(value).value.props.a)
        self.assertEqual(result, [1, 2, 3])

    def test_it_eq(self):
        class Something:
            def __init__(self, value):
                self.value = value

        value = Something({"props": [{"a": 1}, {"a": 2}, {"a": 3}]})
        result = stream(value).value.props.filter(it.a == 2).to_value()
        self.assertEqual(result, {"a": 2})

    def test_lambda(self):
        def func(x):
            return x + 2

        result = stream([1, 2, 3]).map(func).to_list()
        self.assertEqual(result, [3, 4, 5])

    def test_sort(self):
        result = stream([2, 3, 1]).sort().to_list()
        self.assertEqual(result, [1, 2, 3])

    def test_reverse(self):
        result = stream([2, 3, 1]).reverse().to_list()
        self.assertEqual(result, [1, 3, 2])

    def test_distinct(self):
        result = stream([2, 2, 2, 1, 4, 3, 1]).distinct().to_list()
        self.assertEqual(result, [2, 1, 4, 3])

    def test_limit_under(self):
        result = stream(range(200)).limit(10).to_list()
        self.assertEqual(result, list(range(10)))

    def test_limit_over(self):
        result = stream(range(5)).limit(10).to_list()
        self.assertEqual(result, list(range(5)))

    def test_limit_match(self):
        result = stream(range(10)).limit(10).to_list()
        self.assertEqual(result, list(range(10)))


