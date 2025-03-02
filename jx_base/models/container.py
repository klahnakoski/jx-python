# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.utils import enlist

from mo_dots import Data,is_data,is_many
from mo_imports import expect
from mo_logs import Log

ListContainer, Cube, QueryOp = expect("ListContainer", "Cube", "QueryOp")

type2container = Data()
config = Data()  # config.default IS EXPECTED TO BE SET BEFORE CALLS ARE MADE


class Container:

    @staticmethod
    def create(container):
        if isinstance(container, (Container, Cube, ListContainer)):
            return container
        elif is_many(container):
            return ListContainer(name=None, data=container)
        elif is_data(container):
            return ListContainer(name=".", data=enlist(container))
        else:
            Log.error("Do not know how to handle {type}", type=container.__class__.__name__)

    @staticmethod
    def register(name: str, container):
        type2container[name] = container
        if not config.default:
            config.default = name


