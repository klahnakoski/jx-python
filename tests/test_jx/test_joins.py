# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from unittest import skip

from mo_dots import list_to_data, concat_field
from mo_testing.fuzzytestcase import add_error_reporting
from tests.test_jx import BaseTestCase, TEST_TABLE

lots_of_data = list_to_data([{"a": i} for i in range(30)])


@add_error_reporting
class TestJoins(BaseTestCase):
    @skip("Not implemented")
    def test_left_join(self):
        test = {
            "data": [{"a": [{"v": 1}, {"v": 2}], "b": [{}, {"v": 1}]}],
            "query": {"from": [
                {"name": "t", "value": concat_field(TEST_TABLE, "a")},
                {"left_join": {"name": "u", "value": concat_field(TEST_TABLE, "a")}, "on": {"eq": ["t.v", "u.v"]}},
            ]},
            "expecting_list": {"meta": {"format": "list"}, "data": [{"a": [{"v": 1}, {"v": 2}], "b": [{}, {"v": 1}]}]},
        }
        self.utils.execute_tests(test)

    @skip("Not implemented")
    def test_subtraction(self):
        test = {
            "data": [{"a": [{"v": 1}, {"v": 2}], "b": [{}, {"v": 1}]}],
            "query": {
                "select": {"name": ".", "value": "t"},
                "from": [
                    {"name": "t", "value": concat_field(TEST_TABLE, "a")},
                    {"left_join": {"name": "u", "value": concat_field(TEST_TABLE, "a")}, "on": {"eq": ["t.v", "u.v"]}},
                ],
                "where": {"missing": "u"},
            },
            "expecting_list": {"meta": {"format": "list"}, "data": [{"v": 2}],},
        }
        self.utils.execute_tests(test)
