# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

import itertools
import os

import mo_json_config
from jx_base.expressions import QueryOp
from jx_python import jx
from jx_python.containers.list_container import ListContainer
from jx_python.expressions._utils import Python
from mo_dots import *
from mo_files import File
from mo_logs import logger, Except, constants
from mo_logs.exceptions import get_stacktrace
from mo_testing.fuzzytestcase import assertAlmostEqual
from tests import test_jx
from tests.test_jx import TEST_TABLE

logger.static_template = False


class JxTestHarness:
    """
    RUN THE SHARED test_jx CASES AGAINST AN IN-MEMORY jx_python BACKEND.

    THE GENERIC MACHINERY (LOADING CASES, DRIVING THE expecting_* CLAUSES, AND
    FORMAT-AWARE COMPARISON) LIVES HERE.  A DIFFERENT BACKEND (e.g. INTERPRETED
    MODE OVER Data/FlatList) SHOULD SUBCLASS AND OVERRIDE THE EXECUTION SEAM:
    `make_container` AND `execute_query` (AND `execute_update` IF NEEDED).
    """

    # THE Language USED TO NORMALIZE QUERIES FOR EXECUTION AND COMPARISON
    lang = Python

    def __init__(self, kwargs=None):
        self.container = None

    def setUp(self):
        self.container = None

    def tearDown(self):
        self.container = None

    def setUpClass(self):
        pass

    def tearDownClass(self):
        pass

    def not_real_service(self):
        return True

    # ------------------------------------------------------------------ #
    # BACKEND SEAM - OVERRIDE THESE FOR A DIFFERENT EXECUTION STRATEGY
    # ------------------------------------------------------------------ #
    def make_container(self, data):
        """BUILD THE BACKEND CONTAINER FROM THE TEST DATA."""
        return ListContainer(name=".", data=from_data(data))

    def execute_query(self, query):
        query = to_data(query)
        q = to_data(dict(from_data(query)))
        q["from"] = self._resolve_from(query["from"])
        query_op = QueryOp.wrap(q, self.container, self.lang)
        return self.container.query(query_op)

    def execute_update(self, command):
        self.container.update(command)

    # ------------------------------------------------------------------ #
    # GENERIC MACHINERY - SHARED BY ALL BACKENDS
    # ------------------------------------------------------------------ #
    def execute_tests(self, subtest, tjson=False, places=6):
        subtest = to_data(subtest)
        subtest.name = get_stacktrace()[1]["method"]

        if subtest.disable:
            return

        self.fill_container(subtest, typed=tjson)
        self.send_queries(subtest)

    def fill_container(self, subtest, typed=False):
        """LOAD THE TEST DATA INTO THE BACKEND, NAMED TEST_TABLE."""
        subtest = to_data(subtest)
        try:
            self.container = self.make_container(subtest.data)
        except Exception as cause:
            logger.error("can not load {data} into container", data=subtest.data, cause=cause)

        frum = subtest.query["from"]
        if not frum:
            subtest.query["from"] = TEST_TABLE
        return Data(index=TEST_TABLE, alias=TEST_TABLE)

    def _resolve_from(self, frum):
        """REPLACE THE TEST_TABLE NAME WITH THE ACTUAL CONTAINER OBJECT."""
        if isinstance(frum, str) and startswith_field(frum, TEST_TABLE):
            tail = tail_field(frum)[1]
            if not tail:
                return self.container
            return concat_field(".", tail)  # nested path relative to container
        elif is_data(frum):
            return {k: self._resolve_from(v) for k, v in from_data(frum).items()}
        elif is_many(frum):
            return [self._resolve_from(v) for v in frum]
        else:
            return frum

    def send_queries(self, subtest):
        subtest = to_data(subtest)

        try:
            num_expectations = 0
            for k, v in subtest.items():
                if k.startswith("expecting_"):
                    format = k[len("expecting_"):]
                elif k == "expecting":
                    format = None
                else:
                    continue

                num_expectations += 1
                expected = v

                query = to_data(from_data(subtest.query))
                query.format = format
                query.meta.testing = True

                try:
                    result = self.execute_query(query)
                except Exception as cause:
                    cause = Except.wrap(cause)
                    if format == "error":
                        if expected in cause:
                            return
                        else:
                            logger.error(
                                "Query failed, but for wrong reason; expected {expected}, got {reason}",
                                expected=expected, reason=cause,
                            )
                    else:
                        logger.error("did not expect error", cause=cause)

                self.compare_to_expected(query, result, expected)
            if num_expectations == 0:
                logger.error(
                    "Expecting test {name|quote} to have property named 'expecting_*'"
                    " for testing the various format clauses",
                    {"name": subtest.name},
                )
        except Exception as cause:
            logger.error("Failed test {name|quote}", name=subtest.name, cause=cause)

    def compare_to_expected(self, query, result, expect):
        query = to_data(query)
        expect = to_data(expect)

        if result.meta.format == "table":
            assertAlmostEqual(set(result.header), set(expect.header))

            mapping = list(zip(
                *list(zip(
                    *filter(
                        lambda v: v[0][1] == v[1][1],
                        itertools.product(
                            enumerate(expect.header), enumerate(result.header)
                        ),
                    )
                ))[1]
            ))[0]
            result.header = [result.header[m] for m in mapping]

            if result.data:
                columns = list(zip(*from_data(result.data)))
                result.data = list(zip(*[columns[m] for m in mapping]))

            if not query.sort:
                self.sort_table(result)
                self.sort_table(expect)
        elif result.meta.format == "list":
            if query["from"].startswith("meta."):
                pass
            else:
                query = QueryOp.wrap(query, Null, self.lang)

            if not query.sort:
                try:
                    data_columns = jx.sort(
                        set(jx.get_columns(result.data, leaves=True))
                        | set(jx.get_columns(expect.data, leaves=True)),
                        "name",
                    )
                except Exception:
                    data_columns = [{"name": "."}]

                sort_order = listwrap(coalesce(query.edges, query.groupby)) + data_columns

                if is_sequence(expect.data):
                    try:
                        expect.data = jx.sort(expect.data, sort_order.name)
                    except Exception:
                        pass

                if is_many(result.data):
                    try:
                        result.data = jx.sort(result.data, sort_order.name)
                    except Exception as cause:
                        logger.warning("sorting failed", cause=cause)

        elif (
            result.meta.format == "cube"
            and len(result.edges) == 1
            and result.edges[0].name == "rownum"
            and not query.sort
        ):
            result_data, result_header = self.cube2list(result.data)
            result_data = from_data(jx.sort(result_data, result_header))
            result.data = self.list2cube(result_data, result_header)

            expect_data, expect_header = self.cube2list(expect.data)
            expect_data = jx.sort(expect_data, expect_header)
            expect.data = self.list2cube(expect_data, expect_header)

        assertAlmostEqual(result, expect, places=6)

    @staticmethod
    def cube2list(cube):
        header = list(from_data(cube).keys())
        rows = []
        for r in zip(*[[(k, v) for v in a] for k, a in cube.items()]):
            row = Data()
            for k, v in r:
                row[k] = v
            rows.append(from_data(row))
        return rows, header

    @staticmethod
    def list2cube(rows, header):
        output = {h: [] for h in header}
        for r in rows:
            for h in header:
                if h == ".":
                    output[h].append(r)
                else:
                    r = to_data(r)
                    output[h].append(r[h])
        return output

    @staticmethod
    def sort_table(result):
        data = to_data([{str(i): v for i, v in enumerate(row)} for row in result.data])
        sort_columns = jx.sort(set(jx.get_columns(data, leaves=True).name))
        data = jx.sort(data, sort_columns)
        result.data = [
            tuple(row[str(i)] for i in range(len(result.header))) for row in data
        ]


# read_alternate_settings
try:
    default_file = File("tests/config/python.json")
    filename = os.environ.get("TEST_CONFIG")
    config_file = File(filename) if filename else default_file
    logger.alert(
        f"Use TEST_CONFIG environment variable to point to config file.  Using {config_file.abs_path}"
    )
    test_jx.global_settings = mo_json_config.get("file://" + config_file.abs_path)
    constants.set(test_jx.global_settings.constants)

    if not test_jx.global_settings.use:
        logger.error('Must have a {"use": type} set in the config file')

    logger.start(test_jx.global_settings.debug)
    test_jx.utils = JxTestHarness(test_jx.global_settings)
except Exception as cause:
    logger.warning("problem", cause)
