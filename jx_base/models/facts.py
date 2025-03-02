# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from jx_base.language import ID
from mo_future import is_text
from mo_logs import Log


class Facts:
    """
    REPRESENT A HIERARCHICAL DATASTORE: MULTIPLE TABLES IN A DATABASE ALONG
    WITH THE RELATIONS THAT CONNECT THEM ALL, BUT LIMITED TO A TREE
    """


    def __init__(self, name, container):
        if not is_text(name):
            Log.error("parameter is wrong")
        self.container = container
        self.name = name
        setattr(self, ID, -1)

    @property
    def namespace(self):
        return self.container.namespace

    @property
    def snowflake(self):
        return self.schema.snowflake

    @property
    def schema(self):
        return self.container.namespace.get_schema(self.name)
