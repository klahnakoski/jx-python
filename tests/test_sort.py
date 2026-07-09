# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_python import jx
from mo_dots import to_data, Null
from mo_testing.fuzzytestcase import FuzzyTestCase, add_error_reporting


@add_error_reporting
class TestSort(FuzzyTestCase):
    def test_no_args_mixed_types_with_null(self):
        # no sort clause => sort by value; numbers before strings, null sorts last
        result = jx.sort([3, None, "b", 1, "a"])
        self.assertEqual(list(result), [1, 3, "a", "b", None])

    def test_no_args_ints(self):
        self.assertEqual(list(jx.sort([3, 1, 2])), [1, 2, 3])

    def test_no_args_set(self):
        self.assertEqual(list(jx.sort({3, 1, 2})), [1, 2, 3])

    def test_no_args_flatlist(self):
        self.assertEqual(list(jx.sort(to_data([3, 1, 2]))), [1, 2, 3])

    def test_empty_input(self):
        self.assertEqual(list(jx.sort([])), [])

    def test_none_input(self):
        result = jx.sort(None)
        self.assertIs(result, Null)
        self.assertEqual(list(result), [])

    def test_single_fieldname(self):
        result = jx.sort([{"a": 3}, {"a": 1}, {"a": 2}], "a")
        self.assertEqual(list(result), [{"a": 1}, {"a": 2}, {"a": 3}])

    def test_field_sort_descending(self):
        # {"field": ..., "sort": -1} form; regression for missing is_integer import in sort_op
        result = jx.sort([{"a": 1}, {"a": 3}, {"a": 2}], {"field": "a", "sort": -1})
        self.assertEqual(list(result), [{"a": 3}, {"a": 2}, {"a": 1}])

    def test_field_direction_form(self):
        # {field: direction} form, eg {"a": "desc"}
        result = jx.sort([{"a": 1}, {"a": 3}, {"a": 2}], {"a": "desc"})
        self.assertEqual(list(result), [{"a": 3}, {"a": 2}, {"a": 1}])
