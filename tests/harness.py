# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
"""
HARNESSES THAT RUN THE SHARED tests/test_jx CONFORMANCE SUITE AGAINST jx_python.

Two in-memory execution modes, both list-format only (table/cube are the SQL /
service backends' concern):

- PythonHarness      - COMPILES each query to the Python language (generated
                       source via `to_python()` + `compile_expression`), i.e. the
                       normal `ListContainer.query` path.
- InterpretedHarness - INTERPRETS the query by evaluating expressions directly
                       through their `__call__` (tree-walk), no code generation.

A new mode subclasses `JxTestHarness` and implements `execute_query`.
"""

from jx_base.expressions import FilterOp, QueryOp
from jx_python import jx
from jx_python.containers.list_container import ListContainer
from jx_python.expressions._utils import Python
from mo_dots import (
    Data,
    Null,
    coalesce,
    concat_field,
    from_data,
    is_data,
    is_many,
    is_sequence,
    listwrap,
    startswith_field,
    tail_field,
    to_data,
)
from mo_logs import Except, logger
from mo_logs.exceptions import get_stacktrace
from mo_testing.fuzzytestcase import assertAlmostEqual
from tests.test_jx import TEST_TABLE


class JxTestHarness:
    """
    GENERIC MACHINERY: LOAD A CASE, DRIVE ITS expecting_* CLAUSES, COMPARE.
    SUBCLASSES SUPPLY `execute_query` (AND MAY OVERRIDE `make_container`).
    """

    # THE Language USED TO NORMALIZE/EVALUATE QUERIES AND COMPARE RESULTS
    lang = Python
    # FORMATS THIS BACKEND KNOWS HOW TO PRODUCE; OTHERS ARE SKIPPED
    supported_formats = {None, "list"}

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
    # BACKEND SEAM
    # ------------------------------------------------------------------ #
    def make_container(self, data):
        """BUILD THE BACKEND CONTAINER FROM THE TEST DATA."""
        return ListContainer(name=".", data=from_data(data))

    def execute_query(self, query):
        raise NotImplementedError()

    def execute_update(self, command):
        self.container.update(command)

    # ------------------------------------------------------------------ #
    # GENERIC MACHINERY
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
                if format not in self.supported_formats and format != "error":
                    continue  # THIS BACKEND DOES NOT PRODUCE THIS FORMAT

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
        """COMPARE list-FORMAT RESULTS, ORDER-INSENSITIVE UNLESS THE QUERY SORTS."""
        query = to_data(query)
        expect = to_data(expect)

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

        assertAlmostEqual(result, expect, places=6)


class PythonHarness(JxTestHarness):
    """COMPILE EACH QUERY TO THE PYTHON LANGUAGE AND RUN VIA ListContainer.query."""

    def execute_query(self, query):
        query = to_data(query)
        q = to_data(dict(from_data(query)))
        q["from"] = self._resolve_from(query["from"])
        query_op = QueryOp.wrap(q, self.container, self.lang)
        return self.container.query(query_op)


class InterpretedHarness(JxTestHarness):
    """
    INTERPRET THE QUERY: EVALUATE THE `where` PREDICATE DIRECTLY THROUGH ITS
    `__call__` (NO COMPILED PYTHON SOURCE), THEN SHAPE select/sort/format OVER
    THE SURVIVING ROWS.
    """

    def execute_query(self, query):
        query = to_data(query)
        q = to_data(dict(from_data(query)))
        q["from"] = self._resolve_from(query["from"])
        container = self.container

        query_op = QueryOp.wrap(q, container, self.lang)
        rows = FilterOp(container, query_op.where)()

        survivors = ListContainer(name=".", data=rows, schema=container.schema)
        q2 = to_data(dict(from_data(q)))
        q2["where"] = True
        q2["from"] = survivors
        return survivors.query(QueryOp.wrap(q2, survivors, self.lang))
