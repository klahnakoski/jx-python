# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_python import ListContainer
from mo_json import INTEGER, STRING, NUMBER
from mo_testing.fuzzytestcase import FuzzyTestCase, add_error_reporting


@add_error_reporting
class TestLists(FuzzyTestCase):
    def test_list(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": 5, "b": 6}]
        con = ListContainer("test", data)
        columns = con.get_schema().columns
        self.assertEqual(2, len(columns))
        self.assertEqual(columns, [{"name": "a", "json_type": INTEGER}, {"name": "b", "json_type": INTEGER}])

    def test_deep_value_list(self):
        data = [{"a": 1.4, "b": ["a", 3]}, {"a": 4, "b": [5, 6]}]
        con = ListContainer("test", data)
        columns = con.get_schema().columns
        self.assertEqual(1, len(columns))
        self.assertEqual(columns, [{"name": "a", "json_type": NUMBER}])

        deep_columns = con.get_schema("test.b").columns
        self.assertEqual(deep_columns, [{"name": ".", "nested_path": ["test.b", "test"], "json_type": STRING}])

    def test_deep_properties(self):
        data = [{"a": 1.4, "b": {"c": 3, "d": 4}}, {"a": 4, "b": {"c": 5, "d": 6}}]
        con = ListContainer("test", data)
        columns = con.get_schema().columns
        self.assertEqual(3, len(columns))

        self.assertEqual(
            columns,
            [
                {"name": "a", "nested_path": ["test"], "json_type": NUMBER},
                {"name": "b.c", "nested_path": ["test"], "json_type": INTEGER},
                {"name": "b.d", "nested_path": ["test"], "json_type": INTEGER},
            ],
        )

    def test_deep_object_list(self):
        data = [{"a": 1.4, "b": [{"c": 3, "d": 4}, {"c": 5, "d": 6}]}]
        con = ListContainer("test", data)
        columns = con.get_schema().columns
        self.assertEqual(1, len(columns))

        deep_columns = con.get_schema("test.b").columns
        self.assertEqual(
            deep_columns,
            [
                {"name": "c", "nested_path": ["test.b", "test"], "json_type": INTEGER},
                {"name": "d", "nested_path": ["test.b", "test"], "json_type": INTEGER},
            ],
        )

    def test_expand_to_value_array(self):
        data = [{"a": 1, "b": 2}, {"a": 4, "b": [5, 6]}]
        con = ListContainer("test", data)
        columns = con.get_schema().columns
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns, [{"name": "a", "json_type": INTEGER}])

        deep_columns = con.get_schema("test.b").columns
        self.assertEqual(deep_columns, [{"name": ".", "nested_path": ["test.b", "test"], "json_type": INTEGER}])

    def test_expand_to_object_array(self):
        data = [{"a": 1, "b": {"c": 2}}, {"a": 4, "b": [{"c": 5}, {"c": 6}]}]
        con = ListContainer("test", data)
        columns = con.get_schema().columns
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns, [{"name": "a", "json_type": INTEGER}])

        deep_columns = con.get_schema("test.b").columns
        self.assertEqual(deep_columns, [{"name": "c", "nested_path": ["test.b", "test"], "json_type": INTEGER}])

    def test_use_to_object_array(self):
        data = [{"a": 1, "b": [{"c": 5}, {"c": 6}]}, {"a": 4, "b": {"c": 2}}]
        con = ListContainer("test", data)
        columns = con.get_schema().columns
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns, [{"name": "a", "json_type": INTEGER}])

        deep_columns = con.get_schema("test.b").columns
        self.assertEqual(deep_columns, [{"name": "c", "nested_path": ["test.b", "test"], "json_type": INTEGER}])

