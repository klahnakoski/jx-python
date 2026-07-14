# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_files import File
from mo_logs import Log
from mo_testing.fuzzytestcase import FuzzyTestCase

TEST_TABLE = "testdata"

global_settings = None
utils = None


class BaseTestCase(FuzzyTestCase):

    def __init__(self, *args, **kwargs):
        FuzzyTestCase.__init__(self, *args, **kwargs)
        if not utils:
            try:
                import tests
            except Exception as e:
                Log.error("Expecting ./tests/__init__.py with instructions to setup testing", cause=e)
        if utils is None:
            Log.error("Expecting ./tests/__init__.py to set `global_settings` and `utils` so tests can be run")
        self.utils = utils

    @classmethod
    def setUpClass(cls):
        utils.setUpClass()

    @classmethod
    def tearDownClass(cls):
        utils.tearDownClass()

    def setUp(self):
        utils.setUp()

    def tearDown(self):
        utils.tearDown()


for file in File(".").leaves:
    if "__pycache__" in file.abs_path:
        file.delete()
