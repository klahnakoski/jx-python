# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_python import jx
from mo_dots import to_data
from mo_testing.fuzzytestcase import FuzzyTestCase, add_error_reporting


@add_error_reporting
class TestTuple(FuzzyTestCase):
    def test_list_single_field(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        self.assertEqual(list(jx.tuple(data, "a")), [(1,), (3,)])

    def test_flatlist_single_field(self):
        # BUGS.md #4: FlatList input was rejected with "not supported yet"
        data = to_data([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
        self.assertEqual(list(jx.tuple(data, "a")), [(1,), (3,)])

    def test_flatlist_multi_field(self):
        data = to_data([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
        self.assertEqual(list(jx.tuple(data, ["a", "b"])), [(1, 2), (3, 4)])
