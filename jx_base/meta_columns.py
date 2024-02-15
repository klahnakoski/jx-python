# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import datetime

from jx_base import Namespace
from jx_base.data_class import DataClass
from jx_base.models.schema import Schema
from jx_base.models.snowflake import Snowflake
from mo_collections import UniqueIndex
from mo_dots import (
    Data,
    FlatList,
    NullType,
    concat_field,
    to_data,
    is_many,
    is_missing, relative_field,
)
from mo_future import Mapping
from mo_future import binary_type, items, long, none_type, text
from mo_imports import export
from mo_json import (
    INTEGER,
    NUMBER,
    STRING,
    OBJECT,
    true,
    EXISTS,
    ARRAY, python_type_to_json_type,
)
from mo_json.typed_encoder import EXISTS_KEY
from mo_times.dates import Date

DEBUG = False
META_TABLES_NAME = "meta.tables"
META_COLUMNS_NAME = "meta.columns"
META_COLUMNS_TYPE_NAME = "column"
ROOT_PATH = [META_COLUMNS_NAME]
singlton = None


TableDesc = DataClass(
    "Table",
    ["name", {"name": "url", "nulls": true}, "query_path", {"name": "last_updated", "nulls": False}, "columns"],
    constraint={"and": [{"ne": [{"last": "query_path"}, {"literal": "."}]}]},
)

Column = DataClass(
    "Column",
    [
        "name",  # ABS NAME OF COLUMN
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
    constraint={"and": [
        {
            "when": {"ne": {"name": "."}},
            "then": {"or": [
                {"and": [{"eq": {"json_type": OBJECT}}, {"eq": {"multi": 1}}]},
                {"ne": ["name", {"first": "nested_path"}]},
            ]},
            "else": True,
        },
        {"when": {"eq": {"es_column": "."}}, "then": {"in": {"json_type": [ARRAY, OBJECT]}}, "else": True},
        {"not": {"find": {"es_column": "null"}}},
        {"not": {"eq": {"es_column": "string"}}},
        {"not": {"eq": {"es_type": "object", "json_type": EXISTS}}},
        {"when": {"suffix": {"es_column": "." + EXISTS_KEY}}, "then": {"eq": {"json_type": EXISTS}}, "else": True},
        {"when": {"suffix": {"es_column": "." + EXISTS_KEY}}, "then": {"exists": "cardinality"}, "else": True},
        {"when": {"eq": {"json_type": OBJECT}}, "then": {"in": {"cardinality": [0, 1]}}, "else": True},
        {"when": {"eq": {"json_type": ARRAY}}, "then": {"in": {"cardinality": [0, 1]}}, "else": True},
        {"not": {"prefix": [
            {"first": "nested_path"},
            {"literal": "testdata"},
        ]}},  # USED BY THE TEST GENERATOR.  IF THIS EXISTS IN A CONTAINER THEN IT FAILED
        {"ne": [{"last": "nested_path"}, {"literal": "."}]},  # NESTED PATHS MUST BE REAL TABLE NAMES INSIDE Namespace
        {
            "when": {"eq": [{"literal": ".~N~"}, {"right": {"es_column": 4}}]},
            "then": {"or": [
                {"and": [{"gt": {"multi": 1}}, {"eq": {"json_type": ARRAY}}, {"eq": {"es_type": "nested"}}]},
                {"and": [{"eq": {"multi": 1}}, {"eq": {"json_type": OBJECT}}, {"eq": {"es_type": "object"}}]},
            ]},
            "else": True,
        },
        {
            "when": {"gte": [{"count": "nested_path"}, 2]},
            "then": {"ne": [{"first": {"right": {"nested_path": 2}}}, {"literal": "."}]},  # SECOND-LAST ELEMENT
            "else": True,
        },
    ]},
)


def get_schema_from_list(table_name, frum, native_type_to_json_type=python_type_to_json_type):
    """
    SCAN THE LIST FOR COLUMN TYPES
    """

    columns = UniqueIndex(keys=("es_column",))
    snowflake = Snowflake(Namespace(), [table_name], columns)

    _get_schema_from_list(
        frum,
        prefix=".",
        nested_path=[table_name],
        snowflake=snowflake,
        native_type_to_json_type=native_type_to_json_type,
    )
    return Schema([table_name], snowflake)


def _get_schema_from_list(
    frum,  # The list
    prefix,  # path to current property
    nested_path,  # each nested array, in reverse order
    snowflake,
    native_type_to_json_type,  # dict from storage type name to json type name
):
    for row in frum:
        if is_missing(row):
            continue

        full_name = concat_field(nested_path[0], prefix)
        if prefix!="." and full_name in snowflake.query_paths and not is_many(row):
            row = [row]
            es_type = list.__name__
        elif is_many(row):  # GET TYPE OF MULTIVALUE
            v = list(row)
            if len(v) == 1:
                es_type = v[0].__class__.__name__
            else:
                es_type = row.__class__.__name__
        else:
            es_type = row.__class__.__name__

        json_type = native_type_to_json_type(es_type)

        if json_type == ARRAY:
            np = [full_name, *nested_path]
            if full_name not in snowflake.query_paths:
                # find any not-nested columns, and make them nested
                snowflake.query_paths.append(full_name)
                for c in snowflake.columns:
                    if c.es_column.startswith(full_name):
                        c.name = relative_field(c.es_column, full_name)
                        c.nested_path = [full_name, *nested_path]

            _get_schema_from_list(row, ".", np, snowflake, native_type_to_json_type)
        elif json_type == OBJECT:
            for name, value in row.items():
                _get_schema_from_list(
                    [value], concat_field(prefix, name), nested_path, snowflake, native_type_to_json_type,
                )
        else:
            # EXPECTING PRIMITIVE VALUE
            column = snowflake.columns[full_name]
            if not column:
                column = Column(
                    name=prefix,
                    es_column=full_name,
                    es_index=nested_path[0],
                    es_type=es_type,
                    json_type=json_type,
                    last_updated=Date.now(),
                    nested_path=nested_path,
                    multi=1,
                )
                snowflake.columns.add(column)
            else:
                column.es_type = _merge_python_type(column.es_type, row.__class__)
                column.json_type = native_type_to_json_type(column.es_type)


def get_id(column):
    """
    :param column:
    :return: Elasticsearch id for column
    """
    return column.es_index + "|" + column.es_column


META_COLUMNS_DESC = TableDesc(
    name=META_COLUMNS_NAME,
    url=None,
    query_path=ROOT_PATH,
    last_updated=Date.now(),
    columns=to_data([
        *(
            Column(
                name=c,
                es_index=META_COLUMNS_NAME,
                es_column=c,
                es_type="keyword",
                json_type=STRING,
                last_updated=Date.now(),
                nested_path=ROOT_PATH,
                multi=1,
            )
            for c in ["name", "es_type", "json_type", "es_column", "es_index", "partitions"]
        ),
        *(
            Column(
                name=c,
                es_index=META_COLUMNS_NAME,
                es_column=c,
                es_type="integer",
                json_type=INTEGER,
                last_updated=Date.now(),
                nested_path=ROOT_PATH,
                multi=1,
            )
            for c in ["count", "cardinality", "multi"]
        ),
        Column(
            name="nested_path",
            es_index=META_COLUMNS_NAME,
            es_column="nested_path",
            es_type="keyword",
            json_type=STRING,
            last_updated=Date.now(),
            nested_path=ROOT_PATH,
            multi=4,
        ),
        Column(
            name="last_updated",
            es_index=META_COLUMNS_NAME,
            es_column="last_updated",
            es_type="double",
            json_type=NUMBER,
            last_updated=Date.now(),
            nested_path=ROOT_PATH,
            multi=1,
        ),
    ]),
)

META_TABLES_DESC = TableDesc(
    name=META_TABLES_NAME,
    url=None,
    query_path=ROOT_PATH,
    last_updated=Date.now(),
    columns=to_data([
        *(
            Column(
                name=c,
                es_index=META_TABLES_NAME,
                es_column=c,
                es_type="string",
                json_type=STRING,
                last_updated=Date.now(),
                nested_path=ROOT_PATH,
                multi=1,
            )
            for c in ["name", "url", "query_path"]
        ),
        *(
            Column(
                name=c,
                es_index=META_TABLES_NAME,
                es_column=c,
                es_type="integer",
                json_type=INTEGER,
                last_updated=Date.now(),
                nested_path=ROOT_PATH,
                multi=1,
            )
            for c in ["timestamp"]
        ),
    ]),
)


SIMPLE_METADATA_COLUMNS = [  # FOR PURELY INTERNAL PYTHON LISTS, NOT MAPPING TO ANOTHER DATASTORE
    *(
        Column(
            name=c,
            es_index=META_COLUMNS_NAME,
            es_column=c,
            es_type="string",
            json_type=STRING,
            last_updated=Date.now(),
            nested_path=ROOT_PATH,
            multi=1,
        )
        for c in ["table", "name", "type"]
    ),
    *(
        Column(
            name=c,
            es_index=META_COLUMNS_NAME,
            es_column=c,
            es_type="long",
            json_type=INTEGER,
            last_updated=Date.now(),
            nested_path=ROOT_PATH,
            multi=1,
        )
        for c in ["count", "cardinality", "multi"]
    ),
    Column(
        name="last_updated",
        es_index=META_COLUMNS_NAME,
        es_column="last_updated",
        es_type="time",
        json_type=NUMBER,
        last_updated=Date.now(),
        nested_path=ROOT_PATH,
        multi=1,
    ),
    Column(
        name="nested_path",
        es_index=META_COLUMNS_NAME,
        es_column="nested_path",
        es_type="string",
        json_type=STRING,
        last_updated=Date.now(),
        nested_path=ROOT_PATH,
        multi=4,
    ),
]

_merge_order = {
    none_type: 0,
    NullType: 1,
    bool: 2,
    int: 3,
    long: 3,
    Date: 4,
    datetime: 4,
    float: 5,
    text: 6,
    binary_type: 6,
    object: 7,
    dict: 8,
    Mapping: 9,
    Data: 10,
    list: 11,
    FlatList: 12,
}

for k, v in items(_merge_order):
    _merge_order[k.__name__] = v


def _merge_python_type(A, B):
    a = _merge_order[A]
    b = _merge_order[B]

    if a >= b:
        output = A
    else:
        output = B

    if isinstance(output, str):
        return output
    else:
        return output.__name__


export("jx_base.expressions.query_op", Column)
export("jx_python.containers.list", Column)
export("jx_python.containers.list", get_schema_from_list)
