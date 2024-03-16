# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from setuptools import setup

setup(
    author="Kyle Lahnakoski",
    author_email="kyle@lahnakoski.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    description="JSON query expressions using Python",
    extras_require={"tests": ["mo-testing>=7.523.24033"]},
    include_package_data=True,
    install_requires=[
        "mo-collections==5.566.24076",
        "mo-dots==9.565.24076",
        "mo-future==7.546.24057",
        "mo-json==6.566.24076",
        "mo-json-config==4.566.24076",
        "mo-kwargs==7.565.24076",
        "mo-logs==8.566.24076",
        "mo-math==7.565.24076",
        "mo-threads==6.566.24076",
        "mo-times==5.566.24076",
    ],
    license="MPL 2.0",
    long_description=(
        "# jx-python\n\nPython library for JSON Expressions \n\n[![PyPI Latest"
        " Release](https://img.shields.io/pypi/v/jx-python.svg)](https://pypi.org/project/jx-python/)\n[![Build"
        " Status](https://github.com/klahnakoski/jx-python/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/klahnakoski/jx-python/actions/workflows/build.yml)\n[![Coverage"
        " Status](https://coveralls.io/repos/github/klahnakoski/jx-python/badge.svg?branch=dev)](https://coveralls.io/github/klahnakoski/jx-python?branch=dev)\n"
    ),
    long_description_content_type="text/markdown",
    name="jx-python",
    packages=[
        "jx_base",
        "jx_base.expressions",
        "jx_base.models",
        "jx_python.expressions",
        "jx_python.containers",
        "jx_python.cubes",
        "jx_python.lists",
        "jx_python.namespace",
        "jx_python",
        "jx_python.streams",
    ],
    url="https://github.com/klahnakoski/jx-python",
    version="4.567.24076",
)
