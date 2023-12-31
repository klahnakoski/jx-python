from unittest import TestCase

from mo_dots import concat_field
from mo_times import Date

from jx_base import jx_expression
from jx_base.expressions import GtOp, Variable, Literal
from jx_python import Column
from mo_json.types import INTEGER
from mo_logs import Log
from mo_testing.fuzzytestcase import add_error_reporting


@add_error_reporting
class TestVarious(TestCase):
    def test_gt_data(self):
        json = GtOp(Variable("a"), Literal(1)).__data__()
        self.assertEqual(json, {"gt": {"a": 1}})

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


    def test_expr(self):
        expr = jx_expression({
            "when": {"gte": [{"count": "nested_path"}, 2]},
            "then": {"ne": [{"first": {"right": {"nested_path": 2}}}, {"literal": "."}]},  # SECOND-LAST ELEMENT
            "else": True,
        })
        python = expr.to_python(0)

        a = (
            (
                not (is_missing(get_attr(enlist(row0), "nested_path")))
                and not ((
                    (None)
                    if (is_missing(get_attr(enlist(row0), "nested_path")))
                    else ((get_attr(enlist(row0), "nested_path"))[int(max([
                        0,
                        min([
                            len(get_attr(enlist(row0), "nested_path"))
                            if (get_attr(enlist(row0), "nested_path")) != None
                            else None,
                            (
                                len(get_attr(enlist(row0), "nested_path"))
                                if (get_attr(enlist(row0), "nested_path")) != None
                                else None
                            )
                            - (2),
                        ]),
                    ])) : int(
                        len(get_attr(enlist(row0), "nested_path"))
                        if (get_attr(enlist(row0), "nested_path")) != None
                        else None
                    )])
                ) == ".")
            )
            if ((sum(((0 if v == None else 1) for v in get_attr(enlist(row1), "nested_path")), 0)) >= (2))
            else (True)
        )


        print(python)


def typed_column(name, sql_key):
    if len(sql_key) > 1:
        Log.error("not expected")
    return concat_field(name, "$" + sql_key)
