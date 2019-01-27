# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from __future__ import unicode_literals
from setuptools import setup
setup(
    description=str(u'JSON query expressions using Python'),
    license=str(u'MPL 2.0'),
    author=str(u'Kyle Lahnakoski'),
    author_email=str(u'kyle@lahnakoski.com'),
    long_description_content_type=str(u'text/markdown'),
    include_package_data=True,
    classifiers=["Development Status :: 4 - Beta","Topic :: Software Development :: Libraries","Topic :: Software Development :: Libraries :: Python Modules","License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)","Programming Language :: Python :: 2.7"],
    install_requires=["mo-collections>=2.31.19025","mo-dots>=2.32.19026","mo-files>=2.31.19025","mo-future>=2.24.19023","mo-json>=2.33.19026","mo-json-config>=2.34.19026","mo-kwargs>=2.32.19026","mo-logs>=2.31.19025","mo-math>=2.31.19025","mo-testing>=2.31.19025","mo-threads>=2.31.19025","mo-times>=2.31.19025"],
    version=str(u'2.34.19026'),
    url=str(u'https://github.com/klahnakoski/jx-python'),
    packages=["jx_base","jx_python/containers","jx_python/cubes","jx_python/lists","jx_python/namespace","jx_python"],
    long_description=str(u'# jx-python\nPython library for JSON Expressions \n'),
    name=str(u'jx-python')
)