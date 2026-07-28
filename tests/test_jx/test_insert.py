from mo_sqlite import sql_query
from mo_testing.fuzzytestcase import add_error_reporting
from tests.test_jx import BaseTestCase


@add_error_reporting
class TestInsert(BaseTestCase):
    """
    BASIC INSERT TESTS WITH SIMPLE "QUERY" TO VERIFY INSERT
    """

    def test_nested(self):
        self.utils.table.insert([{
            "v": 0,
            "a": {"_b": [{"a": 0, "b": 7}, {"a": 1, "b": 6}, {"a": 2, "b": 5}, {"a": 3, "b": 4},]},
        }])
        db = self.utils.container.db
        name = self.utils.table.name
        self.assertIn(name, db.get_tables().name)
        with db.transaction() as t:
            facts = table2list(t.query(sql_query({"from": name}), raw=True))
            self.assertAlmostEqual(facts, [{"v.$N": 0}])
            branches = table2list(t.query(sql_query({"from": name + ".a._b.$A"}), raw=True))
            self.assertAlmostEqual(
                branches,
                [{"a.$N": 0, "b.$N": 7}, {"a.$N": 1, "b.$N": 6}, {"a.$N": 2, "b.$N": 5}, {"a.$N": 3, "b.$N": 4}],
            )

    def test_nested_w_insert(self):
        self.utils.table.insert([{
            "v": 0,
            "a": {"_b": [{"a": 0, "b": 7}, {"a": 1, "b": 6}, {"a": 2, "b": 5}, {"a": 3, "b": 4},]},
        }])
        self.utils.table.insert([{
            "v": 11,
            "a": {"_b": [{"a": "0", "b": "7"}, {"a": "1", "b": "6"}, {"a": "2", "b": "5", "c": True}]},
        }])

        db = self.utils.container.db
        name = self.utils.table.name
        self.assertIn(name, db.get_tables().name)
        with db.transaction() as t:
            facts = table2list(t.query(sql_query({"from": name}), raw=True))
            self.assertAlmostEqual(facts, [{"v.$N": 0}, {"v.$N": 11}])
            branches = table2list(t.query(sql_query({"from": name + ".a._b.$A"}), raw=True))
            self.assertAlmostEqual(
                branches,
                [
                    {"a.$N": 0.0, "b.$N": 7.0,},
                    {"a.$N": 1.0, "b.$N": 6.0,},
                    {"a.$N": 2.0, "b.$N": 5.0,},
                    {"a.$N": 3.0, "b.$N": 4.0,},
                    {"a.$S": "0", "b.$S": "7",},
                    {"a.$S": "1", "b.$S": "6",},
                    {"a.$S": "2", "b.$S": "5", "c.$B": 1,}
                ]
            )


def table2list(table):
    return [{h: v for h, v in zip(table.header, row)} for row in table.data]
