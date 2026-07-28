# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

import os

import mo_json_config
from mo_files import File
from mo_logs import logger, constants
from tests import test_jx
from tests.harness import InterpretedHarness, PythonHarness

logger.static_template = False

HARNESSES = {
    "python": PythonHarness,       # COMPILE TO PYTHON LANGUAGE
    "interpret": InterpretedHarness,  # INTERPRET VIA EXPRESSION __call__
}

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

    use = test_jx.global_settings.use
    if not use:
        logger.error('Must have a {"use": type} set in the config file')
    if use not in HARNESSES:
        logger.error("Do not know how to test {use|quote}; expecting one of {known}", use=use, known=list(HARNESSES))

    logger.start(test_jx.global_settings.debug)
    test_jx.utils = HARNESSES[use](test_jx.global_settings)
except Exception as cause:
    logger.warning("problem", cause)
