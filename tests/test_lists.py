# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_python import ListContainer
from mo_json import JX_INTEGER, INTEGER
from mo_testing.fuzzytestcase import FuzzyTestCase, add_error_reporting


@add_error_reporting
class TestLists(FuzzyTestCase):


    def test_list(self):
        data = [
            {"a": 1, "b": 2},
            {"a": 3, "b": 4},
            {"a": 5, "b": 6}
        ]
        con = ListContainer("test", data)
        columns = con.get_schema().columns
        self.assertEqual(2, len(columns))
        self.assertEqual(columns, [{"name":"a", "json_type":INTEGER}, {"name":"b", "json_type":INTEGER}])
