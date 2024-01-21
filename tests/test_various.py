from unittest import TestCase

from mo_dots import concat_field
from mo_times import Date

from jx_base import jx_expression, DataClass, Column
from jx_base.expressions import GtOp, Variable, Literal
from jx_python.expression_compiler import compile_expression
from mo_json.types import INTEGER, ARRAY
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

    def test_column_nested_path_expression(self):
        json = {"and": [
            {"ne": [
                {"last": "nested_path"},
                {"literal": "."},
            ]},  # NESTED PATHS MUST BE REAL TABLE NAMES INSIDE Namespace
        ]}

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
            AnotherColumn(
                name="name",
                es_column="es_column.~N~",
                es_index="es_index",
                es_type="es_type",
                json_type=INTEGER,
                multi=1,
                nested_path=".",  # never end with .
                last_updated=Date.now(),
            )

    def test_column(self):
        nested_path = ["."]
        with self.assertRaises(Exception):
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
            nested_path="a",
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
                nested_path="a",
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
                nested_path="a",
                last_updated=Date.now(),
            )

        with self.assertRaises(Exception):
            Column(
                name="name",
                es_column="es_column.~N~",
                es_index="es_index",
                es_type="es_type",
                json_type=INTEGER,
                nested_path="a",
                last_updated=Date.now(),
            )


def typed_column(name, sql_key):
    if len(sql_key) > 1:
        Log.error("not expected")
    return concat_field(name, "$" + sql_key)
