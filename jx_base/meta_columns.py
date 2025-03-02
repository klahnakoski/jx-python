# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from jx_base.expressions._utils import JX, _jx_expression as jx_expression
from jx_base.expressions.variable import QueryOp
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
    is_missing,
    relative_field,
    last,
    endswith_field,
    join_field,
    split_field,
)
from mo_dots.datas import register_data
from mo_future import Mapping
from mo_future import binary_type, items, long, none_type, text
from mo_imports import export
from mo_json import (
    INTEGER,
    NUMBER,
    STRING,
    OBJECT,
    EXISTS,
    ARRAY,
    python_type_to_json_type,
    ARRAY_KEY,
    jx_type_to_json_type,
)
from mo_json.typed_encoder import EXISTS_KEY
from mo_logs import logger
from mo_times.dates import Date

_get = object.__getattribute__
_set = object.__setattr__

DEBUG = False
META_TABLES_NAME = "meta.tables"
META_COLUMNS_NAME = "meta.columns"
META_COLUMNS_TYPE_NAME = "column"
ROOT_PATH = [META_COLUMNS_NAME]
singlton = None


@dataclass
class TableDesc:
    name: str
    url: Optional[str]
    query_path: List[str]
    last_updated: Date
    columns: List[Data]

    def __init__(self, name, url, query_path, last_updated, columns):
        self.name = name
        self.url = url
        self.query_path = query_path
        self.last_updated = last_updated
        self.columns = columns

        if last(query_path) == ".":
            logger.error(f"query_path cannot end with a period: {query_path}")


column_constraint = {"and": [
    # {
    #     "when": {"ne": {"name": "."}},
    #     "then": {"or": [
    #         {"and": [{"eq": {"json_type": OBJECT}}, {"eq": {"multi": 1}}]},
    #         {"ne": ["name", {"first": "nested_path"}]},
    #     ]},
    #     "else": True,
    # },
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
    # {"ne": [{"last": "nested_path"}, {"literal": "."}]},  # NESTED PATHS MUST BE REAL TABLE NAMES INSIDE Namespace
    {
        "when": {"eq": [{"literal": f".{ARRAY_KEY}"}, {"right": {"es_column": 4}}]},
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
]}


class Column(Mapping):
    _slots = [
        "name",
        "es_column",
        "es_index",
        "es_type",
        "json_type",
        "nested_path",
        "count",
        "cardinality",
        "multi",
        "last_updated",
        "partitions",
    ]

    def __init__(
        self,
        *,
        name,  # ABS NAME OF COLUMN
        es_column: str,
        es_index: str,
        es_type: str,
        json_type: str,
        nested_path: List[str],  # AN ARRAY OF PATHS (FROM DEEPEST TO SHALLOWEST) INDICATING THE JSON SUB-ARRAYS
        multi: int,
        last_updated,
        partitions: int = None,
        count: Optional[int] = None,
        cardinality: Optional[int] = None,
    ):
        _set(self, "_checking", True)
        self.name = name
        self.es_column = es_column
        self.es_index = es_index
        self.es_type = es_type
        self.json_type = json_type
        self.nested_path = nested_path
        self.multi = multi
        self.last_updated = last_updated
        self.count = count
        self.cardinality = cardinality
        self.partitions = partitions
        _set(self, "_checking", False)
        self.check()

    def check(self):
        _set(self, "_checking", True)
        try:
            if jx_expression(column_constraint, JX)(self):
                return

            for c in column_constraint["and"]:
                if not jx_expression(c, JX)(self):
                    raise ValueError(f"Constraint {c} failed for {self}")
        finally:
            _set(self, "_checking", False)

    def __getitem__(self, item):
        return _get(self, item)

    get = __getitem__

    def __setattr__(self, key, value):
        if key in Column._slots:
            _set(self, key, value)
            if not _get(self, "_checking"):
                self.check()
        else:
            logger.error(f"Cannot set {key} on {self}")

    def __setitem__(self, key, value):
        _set(self, key, value)

    def __hash__(self):
        return hash((
            self.name,
            self.es_column,
            self.es_index,
            self.es_type,
            self.json_type,
            tuple(self.nested_path),
            self.multi,
            self.last_updated,
            self.partitions,
        ))

    def __len__(self):
        return len(Column._slots)

    def keys(self):
        return Column._slots

    def items(self):
        return ((k, _get(self, k)) for k in Column._slots)

    def values(self):
        return (_get(self, k) for k in Column._slots)

    def __iter__(self):
        return iter(Column._slots)

    def __bool__(self):
        return True


register_data(Column)


def get_schema_from_jx_type(table_name, jx_type):
    """
    ASSUME THE VALUES DO NOT HAVE TYPED PROPERTIES
    :param table_name:
    :param jx_type:
    :return:
    """
    paths, columns = _get_columns_from_jx_type([table_name], jx_type)
    schema = Schema([table_name], Snowflake(None, paths, columns))
    schema.snowflake.namespace = schema.snowflake
    return schema


def _get_columns_from_jx_type(nested_path, jx_type):
    paths = [nested_path[0]]
    columns = []
    for path, type in jx_type.leaves():
        if endswith_field(path, ARRAY_KEY):
            child = concat_field(nested_path[0], join_field(split_field(path)[:-1]))
            more_paths, more_columns = _get_columns_from_jx_type([child, *nested_path], type)
            paths = [*paths, *more_paths]
            columns.extend(more_columns)
            continue
        name = concat_field(relative_field(nested_path[0], nested_path[-1]), path)
        columns.append(Column(
            name=name,  # ABS NAME OF COLUMN
            es_column=name,
            es_index=nested_path[0],
            es_type=type,
            json_type=jx_type_to_json_type(type),
            nested_path=nested_path,
            multi=1,
            last_updated=Date.now(),
        ))
    return paths, columns


def get_schema_from_list(table_name, frum, native_type_to_json_type=python_type_to_json_type):
    """
    SCAN THE LIST FOR COLUMN TYPES
    """
    columns = UniqueIndex(keys=("es_column",))
    snowflake = Snowflake(None, [table_name], columns)
    snowflake.namespace = snowflake

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
        if prefix != "." and full_name in snowflake.query_paths and not is_many(row):
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
            if column:
                column.es_type = _merge_python_type(column.es_type, row.__class__)
                column.json_type = native_type_to_json_type(column.es_type)
                continue

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


def query_metadata(container, query):
    container = container.namespace.columns.denormalized()
    normalized = QueryOp.wrap(query)
    return container.query(normalized)


export("jx_base.expressions.query_op", Column)
export("jx_base.expressions.edges_op", Column)

export("jx_base.expressions.literal", get_schema_from_list)