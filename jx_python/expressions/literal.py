# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import, division, unicode_literals

from mo_dots import from_data
from mo_future import text
from mo_json import json2value

from jx_base.expressions import Literal as Literal_


class Literal(Literal_):
    def to_python(self):
        return text(repr(from_data(json2value(self.json))))
