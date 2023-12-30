from unittest import TestCase

from mo_dots import concat_field
from mo_times import Date

from jx_python import Column
from mo_json.types import INTEGER
from mo_logs import Log


class TestVarious(TestCase):

    def test_column(self):
        nested_path = ["."]
        Column(
            name=".",
            json_type=INTEGER,
            es_type="nested",
            es_column=typed_column(
                concat_field(nested_path[0], "."), "n"
            ),
            es_index="test",
            cardinality=0,
            multi=1,
            nested_path=nested_path,
            last_updated=Date.now(),
        )

def typed_column(name, sql_key):
    if len(sql_key) > 1:
        Log.error("not expected")
    return concat_field(name, "$" + sql_key)