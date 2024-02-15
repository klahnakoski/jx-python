# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from mo_dots import Null, relative_field, set_default, startswith_field, dict_to_data

from jx_base.utils import GUID, enlist, UID
from mo_json import EXISTS, ARRAY, OBJECT, INTERNAL
from mo_json.typed_encoder import untype_path
from mo_logs import Log


class Schema(object):
    """
    A Schema MAPS COLUMN NAMES OF A SINGLE TABLE TO COLUMN INSTANCES THAT MATCH
    """

    def __init__(self, nested_path, snowflake):
        """
        :param nested_path: STACK OF TABLES TO GET HERE, ROOT LAST
        :param snowflake: WHERE THIS SCHEMA BELONGS
        """
        self.nested_path = nested_path
        self.snowflake = snowflake
        self.lookup, self.lookup_leaves, self.lookup_variables = _indexer(
            snowflake.columns, self.snowflake.query_paths[0]
        )

    @property
    def table(self):
        return self.nested_path[0]

    @property
    def columns(self):
        return [c for c in self.snowflake.columns if c.nested_path==self.nested_path]

    def __getitem__(self, column_name):
        cs = self.lookup.get(column_name)
        if cs:
            return list(cs)
        else:
            return [dict_to_data({"es_column": column_name})]

    def items(self):
        return self.lookup.items()

    def get_column(self, name, table=None):
        return self.lookup[name]

    def get_column_name(self, column):
        """
        RETURN THE COLUMN NAME, FROM THE PERSPECTIVE OF THIS SCHEMA
        :param column:
        :return: NAME OF column
        """
        return relative_field(column.name, column.nested_path[0])

    def values(self, name):
        """
        RETURN VALUES FOR THE GIVEN PATH NAME
        :param name:
        :return:
        """
        return list(self.lookup_variables.get(untype_path(name), Null))

    def leaves(self, name):
        """
        RETURN LEAVES OF GIVEN PATH NAME
        pull leaves, considering query_path and namespace
        pull all first-level properties
        pull leaves, including parent leaves
        pull the head of any tree by name
        :param name:
        """
        return self.lookup_leaves.get(untype_path(name), Null)

    def map_to_es(self):
        """
        RETURN A MAP FROM THE NAMESPACE TO THE es_column NAME
        """
        full_name = self.query_path
        return set_default(
            {
                relative_field(c.name, full_name): c.es_column
                for k, cs in self.lookup.items()
                # if startswith_field(k, full_name)
                for c in cs
                if c.json_type not in INTERNAL
            },
            {
                c.name: c.es_column
                for k, cs in self.lookup.items()
                # if startswith_field(k, full_name)
                for c in cs
                if c.json_type not in INTERNAL
            },
        )


def _indexer(columns, nested_path):
    nested_path = enlist(nested_path)
    all_names = set(untype_path(c.es_column) for c in columns)

    lookup_leaves = {}  # ALL LEAF VARIABLES
    for full_name in all_names:
        for c in columns:
            cname = c.es_column
            nfp = untype_path(cname)
            if (
                startswith_field(nfp, full_name)
                and c.json_type not in [EXISTS, OBJECT, ARRAY]
                and (c.es_column != GUID or full_name == GUID)
            ):
                cs = lookup_leaves.setdefault(full_name, set())
                cs.add((relative_field(full_name, cname), c))
                cs = lookup_leaves.setdefault(untype_path(full_name), set())
                cs.add((relative_field(full_name, cname), c))

    lookup_variables = {}  # ALL NOT-NESTED VARIABLES
    for full_name in all_names:
        for c in columns:
            cname = c.es_column
            nfp = untype_path(cname)
            if (
                startswith_field(nfp, full_name)
                and c.es_type not in [EXISTS, OBJECT]
                and (c.es_column != UID or full_name == UID)
                and startswith_field(c.nested_path[0], nested_path[0])
            ):
                cs = lookup_variables.setdefault(full_name, set())
                cs.add(c)
                cs = lookup_variables.setdefault(untype_path(full_name), set())
                cs.add(c)

    relative_lookup = {}
    for c in columns:
        try:
            cname = c.es_column
            cs = relative_lookup.setdefault(cname, set())
            cs.add(c)

            ucname = untype_path(cname)
            cs = relative_lookup.setdefault(ucname, set())
            cs.add(c)
        except Exception as e:
            Log.error("Should not happen", cause=e)

    if len(nested_path) > 1:
        # ADD ABSOLUTE NAMES TO THE NAMESAPCE
        absolute_lookup, more_leaves, more_variables = _indexer(columns, nested_path[1:])
        for k, cs in absolute_lookup.items():
            if k not in relative_lookup:
                relative_lookup[k] = cs
        for k, cs in more_leaves.items():
            if k not in lookup_leaves:
                lookup_leaves[k] = cs
        for k, cs in more_variables.items():
            if k not in lookup_variables:
                lookup_variables[k] = cs

    return relative_lookup, lookup_leaves, lookup_variables
