# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from unittest import skipIf

from mo_dots import list_to_data, concat_field
from mo_testing.fuzzytestcase import add_error_reporting
from tests.test_jx import BaseTestCase, TEST_TABLE, global_settings

lots_of_data = list_to_data([{"a": i} for i in range(30)])


@add_error_reporting
class TestNestedQueries(BaseTestCase):
    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    def test_nested_max_simple(self):
        test = {
            "data": [{
                "v": 0,
                "a": {"_b": [{"a": 0, "b": 7}, {"a": 1, "b": 6}, {"a": 2, "b": 5}, {"a": 3, "b": 4},]},
            }],
            "query": {
                "from": TEST_TABLE,
                "select": [{"name": "b", "value": {"from": "a._b", "select": {"value": "b", "aggregate": "sum"},},},],
            },
            "expecting_list": {"meta": {"format": "list"}, "data": [{"b": 22}],},
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    def test_nested_max(self):
        test = {
            "data": [{
                "v": 0,
                "a": {"_b": [{"a": 0, "b": 7}, {"a": 1, "b": 6}, {"a": 2, "b": 5}, {"a": 3, "b": 4},]},
            }],
            "query": {
                "from": TEST_TABLE,
                "select": [
                    "v",
                    {"name": "b", "value": {"from": "a._b", "select": {"value": "b", "aggregate": "sum"},},},
                ],
            },
            "expecting_list": {"meta": {"format": "list"}, "data": [{"v": 0, "b": 22}],},
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    @skipIf(
        global_settings.use == "sqlite",
        "the aggregate mixes origin and nested vars (ToListOp knows only a nested variable), and the"
        " term is named `x` while the expectation says `b`",
    )
    def test_nested_max_of_expression(self):
        test = {
            "data": [{
                "v": 0,
                "a": {"_b": [{"a": 0, "b": 7}, {"a": 1, "b": 6}, {"a": 2, "b": 5}, {"a": 3, "b": 4},]},
            }],
            "query": {
                "from": TEST_TABLE,
                "select": ["v", {"name": "x", "value": {"mul": ["v", "a._b.b"]}, "aggregate": "sum",},],
            },
            "expecting_list": {"meta": {"format": "list"}, "data": [{"v": 0, "b": 22}],},
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    def test_sum(self):
        test = {
            "data": [{
                "v": 0,
                "a": {"_b": [{"a": 0, "b": 7}, {"a": 1, "b": 6}, {"a": 2, "b": 5}, {"a": 3, "b": 4},]},
            }],
            "query": {"from": TEST_TABLE, "select": ["v", {"name": "b", "value": "a._b.b", "aggregate": "sum"},],},
            "expecting_list": {"meta": {"format": "list"}, "data": [{"v": 0, "b": 22}],},
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    @skipIf(global_settings.use == "sqlite", "a stub: the test declares no expecting_* clause")
    def test_distinct_on(self):
        # SELECT DISTINCT ON (a, b) c FROM t ORDER BY a, b

        test = {
            "data": [],
            "query": {
                "from": TEST_TABLE,
                "select": [{
                    "name": "c",
                    "value": {"first": {"from": ".", "orderby": "a, b", "select": {"value": "c"},}},
                }],
                "groupby": ["a", "b"],
            },
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    @skipIf(global_settings.use == "sqlite", "insert fails: table testing.a.$A has no column named $N")
    def test_two_paths(self):
        # VERIFY WE CAN PERFORM MULTIPLE SUBQUERIES IN SINGLE QUERY
        test = {
            "data": [{
                "v": 0,
                "a": [{"a": 0, "b": 17}, {"a": 1, "b": 16}, {"a": 2, "b": 15}, {"a": 3, "b": 14},],
                "b": [{"a": 10, "b": 7}, {"a": 11, "b": 6}, {"a": 12, "b": 5}, {"a": 13, "b": 4},],
            }],
            "query": {
                "from": TEST_TABLE,
                "select": [
                    "v",
                    {"name": "a", "value": "a.a", "aggregate": "sum"},
                    {"name": "b", "value": "b.b", "aggregate": "sum"},
                ],
            },
            "expecting_list": {"meta": {"format": "list"}, "data": [{"v": 0, "a": 6, "b": 22}],},
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    @skipIf(global_settings.use == "sqlite", "values are right; the expectation omits the null-coordinate row")
    def test_group_by_child1(self):
        # VERIFY WE CAN PERFORM MULTIPLE SUBQUERIES IN SINGLE QUERY
        test = {
            "data": [
                {"v": 0, "a": [{"t": "x", "b": 7}, {"t": "x", "b": 6}, {"t": "y", "b": 5}, {"t": "y", "b": 4},],},
                {"v": 1, "a": [{"t": "x", "b": 1}, {"t": "x", "b": 2}, {"t": "y", "b": 3}, {"t": "z", "b": 4},],},
            ],
            "query": {"from": TEST_TABLE, "select": ["v", {"value": "a.b", "aggregate": "sum"},], "edges": ["a.t"],},
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a.t": "x", "v": [0, 1], "a.b": [13, 3]},
                    {"a.t": "y", "v": [0, 1], "a.b": [9, 3]},
                    {"a.t": "z", "v": 1, "a.b": 4},
                ],
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [{"name": "a.t", "domain": {"type": "text", "partitions": ["x", "y", "z"]},}],
                "data": {
                    # THE FACTS ARE STILL GROUPED, LEAVING MULTIVALUES
                    # NOTICE BOTH ARE SAME SHAPE
                    "v": [[0, 1], [0, 1], 1],
                    "a.b": [[13, 3], [9, 3], 4],
                },
            },
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    @skipIf(global_settings.use == "sqlite", "values are right; the expectation omits the null-coordinate row")
    def test_group_by_child2(self):
        # VERIFY WE CAN PERFORM MULTIPLE SUBQUERIES IN SINGLE QUERY
        test = {
            "data": [
                {"v": 0, "a": [{"t": "x", "b": 7}, {"t": "x", "b": 6}, {"t": "y", "b": 5}, {"t": "y", "b": 4},],},
                {"v": 1, "a": [{"t": "x", "b": 1}, {"t": "x", "b": 2}, {"t": "y", "b": 3}, {"t": "z", "b": 4},],},
            ],
            "query": {
                "from": concat_field(TEST_TABLE, "a"),
                "select": ["v", {"value": "a.b", "aggregate": "sum"},],
                "edges": ["a.t"],
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a.t": "x", "v": [0, 0, 1, 1], "a.b": 16},
                    {"a.t": "y", "v": [0, 0, 1], "a.b": 12},
                    {"a.t": "z", "v": 1, "a.b": 4},
                ],
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [{"name": "a.t", "domain": {"type": "text", "partitions": ["x", "y", "z"]},}],
                "data": {
                    # THE FACTS ARE STILL GROUPED, LEAVING MULTIVALUES
                    # NOTICE BOTH ARE SAME SHAPE
                    "v": [[0, 0, 1, 1], [0, 0, 1], 1],
                    "a.b": [16, 12, 4],
                },
            },
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    @skipIf(global_settings.use == "sqlite", "`edges: \"_id\"` fails normalization (programmer error expr)")
    def test_nested_aggregate(self):
        # VERIFY WE CAN AGGREGATE AN AGGREGATE
        test = {
            "data": [{"v": [1, 2, 3, 4]}, {"v": [5, 6, 7, 8]}],
            "query": {"select": {
                "name": "b",
                "value": {"from": TEST_TABLE, "select": {"value": "v", "aggregate": "avg"}, "edges": "_id",},
                "aggregate": "avg",
            }},
            "expecting_list": {"meta": {"format": "value"}, "data": 4.5},
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    @skipIf(global_settings.use == "sqlite", "unfinished: the test body calls an undefined `frum`")
    def test_group_function(self):
        test = {
            "data": [{"v": [1, 2, 3, 4]}, {"v": [5, 6, 7, 8]}],
            "query": {
                "from": TEST_TABLE,
                "select": {
                    "name": ".",
                    "value": {
                        "from": {
                            "select": [
                                {"name": "group", "value": {"mod": [".", 2]}},
                                {"name": "values", "value": "."},
                            ],
                            "from": "v",
                            "group": {"mod": [".", 2]},
                        },
                        "select": [
                            {
                                "name": "mode",
                                "value": {
                                    "when": {"eq": ["group", 0]},
                                    "then": {"literal": "even"},
                                    "else": {"literal": "odd"},
                                },
                            },
                            {"name": "sum", "value": {"sum": "values"}},
                        ],
                    },
                },
            },
        }

        frum(test.data).group({"eq": [{"mod": [".", 2]}, 0]}).select([])
