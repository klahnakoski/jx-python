# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#



from unittest import skipIf, skip

from jx_base.expressions import NULL
from mo_dots import list_to_data, concat_field
from mo_sql.utils import SQL_STRING_KEY
from mo_testing.fuzzytestcase import add_error_reporting
from tests.test_jx import BaseTestCase, TEST_TABLE, global_settings

lots_of_data = list_to_data([{"a": i} for i in range(30)])


@add_error_reporting
class TestFilters(BaseTestCase):
    def test_where_expression(self):
        test = {
            "data": [  # PROPERTIES STARTING WITH _ ARE NESTED AUTOMATICALLY
                {"a": {"b": 0, "c": 0}},
                {"a": {"b": 0, "c": 1}},
                {"a": {"b": 1, "c": 0}},
                {"a": {"b": 1, "c": 1}},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": ["a.b", "a.c"]},
                "sort": "a.b"
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [
                {"a.b": 0, "a.c": 0},
                {"a.b": 1, "a.c": 1},
            ]},
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a.b", "a.c"],
                "data": [[0, 0], [1, 1]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "rownum",
                        "domain": {"type": "rownum", "min": 0, "max": 2, "interval": 1}
                    }
                ],
                "data": {
                    "a.b": [0, 1],
                    "a.c": [0, 1]
                }
            }
        }
        self.utils.execute_tests(test)

    def test_add_expression(self):
        test = {
            "data": [  # PROPERTIES STARTING WITH _ ARE NESTED AUTOMATICALLY
                {"a": {"b": 0, "c": 0}},
                {"a": {"b": 0, "c": 1}},
                {"a": {"b": 1, "c": 0}},
                {"a": {"b": 1, "c": 1}},
            ],
            "query": {
                "select": "*",
                "from": TEST_TABLE,
                "where": {"eq": [{"add": ["a.b", 1]}, "a.c"]},
                "sort": "a.b"
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [
                    {"a.b": 0, "a.c": 1}
                ]
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a.b", "a.c"],
                "data": [[0, 1]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [
                    {
                        "name": "rownum",
                        "domain": {"type": "rownum", "min": 0, "max": 1, "interval": 1}
                    }
                ],
                "data": {
                    "a.b": [0],
                    "a.c": [1]
                }
            }
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    def test_regexp_expression(self):
        test = {
            "data": [{"_a": [
                {"a": "abba"},
                {"a": "aaba"},
                {"a": "aaaa"},
                {"a": "aa"},
                {"a": "aba"},
                {"a": "aa"},
                {"a": "ab"},
                {"a": "ba"},
                {"a": "a"},
                {"a": "b"}
            ]}],
            "query": {
                "from": concat_field(TEST_TABLE, "_a"),
                "select": "*",
                "where": {"regex": {"a": ".*b.*"}},
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"a": "abba"},
                    {"a": "aaba"},
                    {"a": "aba"},
                    {"a": "ab"},
                    {"a": "ba"},
                    {"a": "b"}
                ]
            }
        }
        self.utils.execute_tests(test)

    def test_empty_or(self):
        test = {
            "data": [{"a": 1}],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"or": []}
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": []
            }
        }
        self.utils.execute_tests(test)

    def test_empty_and(self):
        test = {
            "data": [{"a": 1}],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"and": []}
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"a": 1}]
            }
        }
        self.utils.execute_tests(test)

    def test_empty_in(self):
        test = {
            "data": [{"a": 1}],
            "query": {
                "select": "a",
                "from": TEST_TABLE,
                "where": {"in": {"a": []}}
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": []
            }
        }
        self.utils.execute_tests(test)

    def test_in_w_set(self):
        # ENSURE THE SET IS RECOGNIZED LIKE A LIST
        test = {
            "data": [{"a": 1}, {"a": 2}, {"a": 4}],
            "query": {
                "select": "a",
                "from": TEST_TABLE,
                "where": {"in": {"a": {1, 3}}}
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [1]
            }
        }
        self.utils.execute_tests(test)

    def test_where_coalesce(self):
        # coalesce returns the first non-null term
        test = {
            "data": [
                {"a": None, "b": 5},
                {"a": 3, "b": 5},
                {"a": None, "b": 1},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"coalesce": ["a", "b"]}, 5]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"b": 5}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_concat(self):
        # concat joins its (existing) terms with the separator
        test = {
            "data": [
                {"s": "hello"},
                {"s": "world"},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"concat": {"s": "!"}}, {"literal": "hello!"}]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"s": "hello"}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_mod(self):
        # mod is the remainder operator; a null operand makes it null (decisive),
        # so those rows drop out
        test = {
            "data": [
                {"x": 5, "y": 2},
                {"x": 4, "y": 2},
                {"x": 5, "y": None},   # null divisor -> null
                {"x": None, "y": 2},   # null dividend -> null
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"mod": ["x", "y"]}, 1]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": 5, "y": 2}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_mod_negative_dividend(self):
        # negative dividend, positive divisor: remainder follows the divisor sign,
        # so -7 % 3 == 2
        test = {
            "data": [
                {"x": -7, "y": 3},   # 2
                {"x": -8, "y": 3},   # 1
                {"x": -9, "y": 3},   # 0
                {"x": -7, "y": None},  # null -> null
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"mod": ["x", "y"]}, 2]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": -7, "y": 3}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_mod_negative_dividend_zero(self):
        # negative dividend evenly divisible: -9 % 3 == 0
        test = {
            "data": [
                {"x": -9, "y": 3},   # 0
                {"x": -8, "y": 3},   # 1
                {"x": -7, "y": 3},   # 2
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"mod": ["x", "y"]}, 0]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": -9, "y": 3}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_abs(self):
        # abs returns the magnitude
        test = {
            "data": [
                {"n": -3},
                {"n": 5},
                {"n": -1},
                {"n": None},   # null -> null
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"abs": "n"}, 3]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"n": -3}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_floor(self):
        # floor rounds down to the nearest whole number (default modulus 1)
        test = {
            "data": [
                {"f": 2.7},
                {"f": 9.1},
                {"f": 2.1},
                {"f": None},   # null -> null
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"floor": "f"}, 2]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"f": 2.7}, {"f": 2.1}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_pow(self):
        # pow raises lhs to the power of rhs
        test = {
            "data": [
                {"x": 2, "y": 3},
                {"x": 2, "y": 2},
                {"x": 3, "y": 2},
                {"x": 2, "y": None},   # null exponent -> null
                {"x": None, "y": 3},   # null base -> null
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"pow": ["x", "y"]}, 8]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": 2, "y": 3}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_power_alias(self):
        # "power" is an alias for pow
        test = {
            "data": [
                {"x": 2, "y": 3},
                {"x": 3, "y": 2},
                {"x": None, "y": 3},   # null -> null
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"power": ["x", "y"]}, 8]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": 2, "y": 3}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_add(self):
        # add() in a where must compile (multi-operand sum over the terms)
        test = {
            "data": [
                {"a": 2, "b": 3},
                {"a": 1, "b": 1},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"add": ["a", "b"]}, 5]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"a": 2, "b": 3}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_count_collection(self):
        # count() over a multi-valued field = number of existing values in it
        test = {
            "data": [
                {"id": 1, "arr": [1, 2, 3]},
                {"id": 2, "arr": [7]},
                {"id": 3, "arr": [5, 5, 9]},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "id",
                "where": {"eq": [{"count": "arr"}, 3]},
            },
            "expecting_list": {"meta": {"format": "list"}, "data": [1, 3]},
        }
        self.utils.execute_tests(test)

    def test_where_cardinality_collection(self):
        # cardinality() over a multi-valued field = number of distinct values
        test = {
            "data": [
                {"id": 1, "arr": [1, 2, 3]},
                {"id": 2, "arr": [7]},
                {"id": 3, "arr": [5, 5, 9]},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "id",
                "where": {"eq": [{"cardinality": "arr"}, 2]},
            },
            "expecting_list": {"meta": {"format": "list"}, "data": [3]},
        }
        self.utils.execute_tests(test)

    def test_where_max(self):
        # max(...) is decisive: it takes the largest present value, skipping nulls
        test = {
            "data": [
                {"a": 6, "b": 2},
                {"a": 1, "b": 9},
                {"a": 6, "b": None},  # null skipped -> max is 6
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"max": ["a", "b"]}, 6]},
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [{"a": 6, "b": 2}, {"a": 6, "b": None}],
            },
        }
        self.utils.execute_tests(test)

    def test_where_div_by_zero_and_null(self):
        # div is decisive: dividing by zero or by null yields null, not an error
        test = {
            "data": [
                {"a": 6, "b": 2},
                {"a": 6, "b": 0},
                {"a": 6, "b": None},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"div": ["a", "b"]}, 3]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"a": 6, "b": 2}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_value_identity(self):
        # value() is a no-op wrapper: value(v) == v
        test = {
            "data": [
                {"x": 5},
                {"x": 6},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"value": "x"}, 5]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": 5}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_to_text(self):
        # text() coerces to a string; a whole-number float normalises to the int
        # string (2.0 -> "2", not "2.0"); 2.5 -> "2.5"; a missing value stays null
        test = {
            "data": [
                {"x": 2},     # int -> "2"
                {"x": 2.0},   # whole float -> "2"
                {"x": 2.5},   # -> "2.5"
                {"x": 5},     # -> "5"
                {"x": None},  # -> null
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"text": "x"}, {"literal": "2"}]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": 2}, {"x": 2.0}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_to_integer(self):
        # integer() truncates to an int; a null stays null (decisive)
        test = {
            "data": [
                {"x": "5"},
                {"x": 2.9},
                {"x": 7},
                {"x": None},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"integer": "x"}, 2]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": 2.9}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_is_number_eq(self):
        # is_number wrapped in eq must compile (the type predicate lowers to a
        # lang-consistent op); is_number(v) returns v, so eq 5 keeps x == 5
        test = {
            "data": [
                {"x": 5},
                {"x": 25},
                {"x": 2},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"is_number": "x"}, 5]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": 5}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_is_boolean(self):
        # is_boolean returns the boolean value, null for non-booleans; as a where
        # predicate that keeps the True row (False is a boolean but tests falsy)
        test = {
            "data": [
                {"x": True},
                {"x": False},
                {"x": 5},
                {"x": "y"},
                {"x": None},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"is_boolean": "x"},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": True}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_is_integer(self):
        # is_integer keeps rows whose value is an integer (not float, text, bool, null)
        test = {
            "data": [
                {"x": 5},
                {"x": 2.7},
                {"x": "5"},
                {"x": True},
                {"x": None},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"is_integer": "x"},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": 5}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_is_number(self):
        # is_number keeps rows whose value is numeric (not text, bool, or null)
        test = {
            "data": [
                {"x": 5},
                {"x": "hello"},
                {"x": 2.5},
                {"x": True},
                {"x": None},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"is_number": "x"},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": 5}, {"x": 2.5}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_number_coercion(self):
        # number() coerces a string to its numeric value (null if not a number)
        test = {
            "data": [
                {"s": "5"},
                {"s": "9"},
                {"s": "x"},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"number": "s"}, 5]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"s": "5"}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_and_non_boolean_term(self):
        # a non-boolean term of `and` becomes true iff it exists (and is not False)
        test = {
            "data": [
                {"x": 5, "g": 9},
                {"x": 5},
                {"x": 6, "g": 9},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"and": [{"eq": {"x": 5}}, "g"]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"x": 5, "g": 9}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_or_non_boolean_term(self):
        # a non-boolean term of `or` becomes true iff it exists (and is not False)
        test = {
            "data": [
                {"g": 9},
                {"h": 1},
                {"other": 2},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"or": ["g", "h"]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"g": 9}, {"h": 1}]
            }
        }
        self.utils.execute_tests(test)

    def test_where_count_decisive(self):
        # count(...) is the decisive tally: a missing term (absent or null) is
        # skipped, not poisoning the whole count
        test = {
            "data": [
                {"a": 3, "b": 4},
                {"a": 3},  # b absent -> skipped, count == 3
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"eq": [{"count": ["a", "b"]}, 2]},
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"a": 3, "b": 4}]
            }
        }
        self.utils.execute_tests(test)

    def test_in_w_missing_column(self):
        # ENSURE THE SET IS RECOGNIZED LIKE A LIST
        test = {
            "data": [{"a": 1}, {"a": 2}, {"a": 4}],
            "query": {
                "select": "a",
                "from": TEST_TABLE,
                "where": {"in": {"b": [1, 3]}}
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": []
            }
        }
        self.utils.execute_tests(test)

    def test_empty_match_all(self):
        test = {
            "data": [{"a": 1}],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"match_all": {}}
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"a": 1}]
            }
        }
        self.utils.execute_tests(test)

    def test_empty_prefix(self):
        test = {
            "data": [{"v": "test"}],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"prefix": {"v": ""}}
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"v": "test"}]
            }
        }
        self.utils.execute_tests(test)

    def test_null_prefix(self):
        test = {
            "data": [{"v": "test"}],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": {"prefix": {"v": None}}
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"v": "test"}]
            }
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    def test_edges_and_empty_prefix(self):
        test = {
            "data": [{"v": "test"}],
            "query": {
                "from": TEST_TABLE,
                "edges": "v",
                "where": {"prefix": {"v": ""}}
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"v": "test", "count": 1},
                    {"v": NULL, "count": 0}
                ]
            }
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    def test_edges_and_null_prefix(self):
        test = {
            "data": [{"v": "test"}],
            "query": {
                "from": TEST_TABLE,
                "edges": "v",
                "where": {"prefix": {"v": None}}
            },
            "expecting_list": {
                "meta": {"format": "list"},
                "data": [
                    {"v": "test", "count": 1},
                    {"v": NULL, "count": 0}
                ]
            }
        }
        self.utils.execute_tests(test)

    def test_suffix(self):
        test = {
            "data": [
                {"v": "this-is-a-test"},
                {"v": "this-is-a-vest"},
                {"v": "test"},
                {"v": ""},
                {"v": None}
            ],
            "query": {
                "from": TEST_TABLE,
                "where": {"suffix": {"v": "test"}}
            },
            "expecting_list": {
                "meta": {
                    "format": "list"},
                "data": [
                    {"v": "this-is-a-test"},
                    {"v": "test"}
                ]
            }
        }
        self.utils.execute_tests(test)

    def test_null_suffix(self):
        test = {
            "data": [
                {"v": "this-is-a-test"},
                {"v": "this-is-a-vest"},
                {"v": "test"},
                {"v": ""},
                {"v": None}
            ],
            "query": {
                "from": TEST_TABLE,
                "where": {"postfix": {"v": None}}
            },
            "expecting_list": {
                "meta": {
                    "format": "list"},
                "data": [
                    {"v": "this-is-a-test"},
                    {"v": "this-is-a-vest"},
                    {"v": "test"},
                    {"v": NULL},
                    {"v": NULL}
                ]
            }
        }
        self.utils.execute_tests(test)

    def test_empty_suffix(self):
        test = {
            "data": [
                {"v": "this-is-a-test"},
                {"v": "this-is-a-vest"},
                {"v": "test"},
                {"v": ""},
                {"v": None}
            ],
            "query": {
                "from": TEST_TABLE,
                "where": {"postfix": {"v": ""}}
            },
            "expecting_list": {
                "meta": {
                    "format": "list"},
                "data": [
                    {"v": "this-is-a-test"},
                    {"v": "this-is-a-vest"},
                    {"v": "test"},
                    {"v": NULL},
                    {"v": NULL}
                ]
            }
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    def test_eq_with_boolean(self):
        test = {
            "data": [
                {"v": True},
                {"v": True},
                {"v": True},
                {"v": False},
                {"v": False},
                {"v": False},
                {"v": None},
                {"v": None},
                {"v": None}
            ],
            "query": {
                "from": TEST_TABLE,
                "where": {"eq": {"v": "T"}}
            },
            "expecting_list": {
                "meta": {
                    "format": "list"
                },
                "data": [
                    {"v": True},
                    {"v": True},
                    {"v": True}
                ]
            }
        }
        self.utils.execute_tests(test)

    def test_big_integers_in_script(self):
        bigger_than_int32 = 1547 * 1000 * 1000 * 1000
        test = {
            "data": [
                {"v": 42}
            ],
            "query": {
                "from": TEST_TABLE,
                "where": {"lt": [0, {"mul": ["v", bigger_than_int32]}]}  # SOMETHING COMPLICATED ENOUGH TO FORCE SCRIPTING
            },
            "expecting_list": {
                "meta": {
                    "format": "list"
                },
                "data": [
                    {"v": 42}
                ]
            }
        }
        self.utils.execute_tests(test)

    def test_where_is_array(self):
        test = {
            "data": [
                {"a": 1, "b": 1},
                {"a": 1, "b": 2},
                {"a": 2, "b": 1},
                {"a": 2, "b": 2}
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "*",
                "where": [{"eq": {"a": 1}}, {"eq": {"b": 1}}]
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": [{"a": 1, "b": 1}]
            }
        }
        self.utils.execute_tests(test)

    def test_in_using_tuple_of_literals(self):
        test = {
            "data": [
                {"a": "1"},
                {"a": "2"},
                {"a": "3"},
                {"a": "4"},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "a",
                "where": {"in": ["a", [{"literal": "4"}, {"literal": "2"}]]},
                "sort": "a"
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": ["2", "4"]
            }
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use in {"python", "interpret"}, "jx_python known failure")
    def test_eq_using_tuple_of_literals(self):
        test = {
            "data": [
                {"a": "1"},
                {"a": "2"},
                {"a": "3"},
                {"a": "4"},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": "a",
                "where": {"eq": ["a", [{"literal": "4"}, {"literal": "2"}]]},
                "sort": "a"
            },
            "expecting_list": {
                "meta": {"format": "list"}, "data": ["2", "4"]
            }
        }
        self.utils.execute_tests(test)

    @skipIf(not global_settings.elasticsearch.version, "only for ES")
    def test_find_uses_regex_es(self):
        test = {
            "data": [
                {"v": "this-is-a-test"},
                {"v": "this-is-a-vest"},
                {"v": "test"},
                {"v": ""},
                {"v": None}
            ],
            "query": {
                "from": TEST_TABLE,
                "where": {"find": {"v": "test"}}
            },
            "expecting_list": {
                "meta": {
                    "format": "list",
                    "es_query": {
                        "from": 0,
                        "query": {"regexp": {"v."+SQL_STRING_KEY: ".*test.*"}},
                        "size": 10
                    },
                },
                "data": [
                    {"v": "this-is-a-test"},
                    {"v": "test"},
                ]
            }
        }
        self.utils.execute_tests(test)

    def test_find(self):
        test = {
            "data": [
                {"v": "this-is-a-test"},
                {"v": "this-is-a-vest"},
                {"v": "test"},
                {"v": ""},
                {"v": None}
            ],
            "query": {
                "from": TEST_TABLE,
                "where": {"find": {"v": "test"}}
            },
            "expecting_list": {
                "data": [
                    {"v": "this-is-a-test"},
                    {"v": "test"},
                ]
            }
        }
        self.utils.execute_tests(test)

