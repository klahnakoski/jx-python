from unittest import TestCase

from jx_python.expression_compiler import compile_expression
from mo_dots import concat_field
from mo_times import Date

from jx_base import jx_expression, DataClass
from jx_base.expressions import GtOp, Variable, Literal
from jx_python import Column
from mo_json.types import INTEGER, ARRAY, EXISTS_KEY, OBJECT, EXISTS
from mo_logs import Log
from mo_testing.fuzzytestcase import add_error_reporting


@add_error_reporting
class TestVarious(TestCase):
    def test_gt_data(self):
        json = GtOp(Variable("a"), Literal(1)).__data__()
        self.assertEqual(json, {"gt": {"a": 1}})

    def test_ne_expression(self):
        json = {"ne": {"name": "."}}
        code = jx_expression(json).to_python()
        row0 = {"name": "a"}
        func = compile_expression(code)
        result = func(row0)
        self.assertEqual(result, True)

    def test_eq_expression(self):
        json = {"eq": {"name": "."}}
        code = jx_expression(json).to_python()
        row0 = {"name": "."}
        func = compile_expression(code)
        result = func(row0)
        self.assertEqual(result, True)


    def test_expression(self):
        json = {"and": [
            # {
            #     "when": {"ne": {"name": "."}},
            #     "then": {"or": [
            #         {"and": [{"eq": {"json_type": "object"}}, {"eq": {"multi": 1}}]},
            #         {"ne": ["name", {"first": "nested_path"}]},
            #     ]},
            #     "else": True,
            # },
            # {"when": {"eq": {"es_column": "."}}, "then": {"in": {"json_type": ["nested", "object"]}}, "else": True},
            # {"not": {"find": {"es_column": "null"}}},
            # {"not": {"eq": {"es_column": "string"}}},
            # {"not": {"eq": {"es_type": "object", "json_type": "exists"}}},
            # {"when": {"suffix": {"es_column": "." + EXISTS_KEY}}, "then": {"eq": {"json_type": EXISTS}}, "else": True},
            # {"when": {"suffix": {"es_column": "." + EXISTS_KEY}}, "then": {"exists": "cardinality"}, "else": True},
            # {"when": {"eq": {"json_type": OBJECT}}, "then": {"in": {"cardinality": [0, 1]}}, "else": True},
            # {"when": {"eq": {"json_type": ARRAY}}, "then": {"in": {"cardinality": [0, 1]}}, "else": True},
            # {"not": {"prefix": [{"first": "nested_path"}, {"literal": "testdata"}]}},
            {"ne": [
                {"last": "nested_path"},
                {"literal": "."},
            ]},  # NESTED PATHS MUST BE REAL TABLE NAMES INSIDE Namespace
            # {
            #     "when": {"eq": [{"literal": ".~N~"}, {"right": {"es_column": 4}}]},
            #     "then": {"or": [
            #         {"and": [{"gt": {"multi": 1}}, {"eq": {"json_type": "nested"}}, {"eq": {"es_type": "nested"}}]},
            #         {"and": [{"eq": {"multi": 1}}, {"eq": {"json_type": "object"}}, {"eq": {"es_type": "object"}}]},
            #     ]},
            #     "else": True,
            # },
            # {
            #     "when": {"gte": [{"count": "nested_path"}, 2]},
            #     "then": {"ne": [{"first": {"right": {"nested_path": 2}}}, {"literal": "."}]},  # SECOND-LAST ELEMENT
            #     "else": True,
            # },
        ]}
        code = jx_expression(json).to_python(0)
        nested_path = ["."]
        column = Column(
            name=".",
            json_type=INTEGER,
            es_type="nested",
            es_column=typed_column(concat_field(nested_path[0], "."), "n"),
            es_index="test",
            cardinality=0,
            multi=1,
            nested_path=nested_path,
            last_updated=Date.now(),
        )
        func = compile_expression(code)
        result = func(column)
        self.assertEqual(result, False)

        AnotherColumn = DataClass(
            "AnotherColumn",
            [
                "name",
                "es_column",
                "es_index",
                "es_type",
                "json_type",
                "nested_path",  # AN ARRAY OF PATHS (FROM DEEPEST TO SHALLOWEST) INDICATING THE JSON SUB-ARRAYS
                {"name": "count", "nulls": True},
                {"name": "cardinality", "nulls": True},
                {"name": "multi", "nulls": False},
                {"name": "partitions", "nulls": True},
                "last_updated",
            ],
            json
        )
        with self.assertRaises(Exception):
            column = AnotherColumn(
                name=".",
                json_type=INTEGER,
                es_type="nested",
                es_column=typed_column(concat_field(nested_path[0], "."), "n"),
                es_index="test",
                cardinality=0,
                multi=1,
                nested_path=nested_path,
                last_updated=Date.now(),
            )

    def test_column(self):
        nested_path = ["."]
        Column(
            name=".",
            json_type=INTEGER,
            es_type="nested",
            es_column=typed_column(concat_field(nested_path[0], "."), "n"),
            es_index="test",
            cardinality=0,
            multi=1,
            nested_path=nested_path,
            last_updated=Date.now(),
        )

    def test_column_constraints(self):
        multi = Column(
            name="name",
            es_column="es_column.~N~",
            es_index="es_index",
            es_type="nested",
            json_type=ARRAY,
            cardinality=1,
            multi=2,
            nested_path=".",
            last_updated=Date.now(),
        )

        with self.assertRaises(Exception):
            Column(
                name="name",
                es_column="es_column.~N~",
                es_index="es_index",
                es_type="es_type",
                json_type=INTEGER,
                multi=1,
                nested_path=".",  # never end with .
                last_updated=Date.now(),
            )

        with self.assertRaises(Exception):
            Column(
                name="name",
                es_column="es_column.~N~",
                es_index="es_index",
                es_type="es_type",
                json_type=INTEGER,
                multi=0,
                nested_path=".",
                last_updated=Date.now(),
            )

        with self.assertRaises(Exception):
            Column(
                name="name",
                es_column="es_column.~N~",
                es_index="es_index",
                es_type="es_type",
                json_type=INTEGER,
                nested_path=".",
                last_updated=Date.now(),
            )


def typed_column(name, sql_key):
    if len(sql_key) > 1:
        Log.error("not expected")
    return concat_field(name, "$" + sql_key)
