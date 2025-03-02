# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.models.schema import Schema

from mo_dots import startswith_field


class Snowflake:
    """
    REPRESENT ONE ALIAS, AND ITS NESTED ARRAYS
    """

    def __init__(self, namespace, query_paths, columns):
        self.namespace = namespace
        self.query_paths = query_paths
        self.columns = columns

    def get_schema(self, query_path):
        nested_path = []
        for step in self.query_paths:
            if startswith_field(query_path, step):
                nested_path.append(step)

        return Schema(nested_path, self)
