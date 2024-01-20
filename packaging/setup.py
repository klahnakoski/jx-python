# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from setuptools import setup
setup(
    author='Kyle Lahnakoski',
    author_email='kyle@lahnakoski.com',
    classifiers=["Development Status :: 4 - Beta","Topic :: Software Development :: Libraries","Topic :: Software Development :: Libraries :: Python Modules","License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)","Programming Language :: Python :: 3.8","Programming Language :: Python :: 3.9","Programming Language :: Python :: 3.11","Programming Language :: Python :: 3.12"],
    description='JSON query expressions using Python',
    extras_require={"tests":["mo-testing"]},
    include_package_data=True,
    install_requires=["mo-collections==5.486.24020","mo-dots==9.476.24007","mo-future==7.476.24007","mo-json==6.486.24020","mo-json-config==4.487.24020","mo-kwargs==7.476.24007","mo-logs==8.477.24007","mo-math==7.476.24007","mo-times==5.481.24007"],
    license='MPL 2.0',
    long_description='# jx-python\nPython library for JSON Expressions \n',
    long_description_content_type='text/markdown',
    name='jx-python',
    packages=["jx_base","jx_base.expressions","jx_base.models","jx_python.expressions","jx_python.containers","jx_python.cubes","jx_python.lists","jx_python.namespace","jx_python","jx_python.streams"],
    url='https://github.com/klahnakoski/jx-python',
    version='4.488.24020'
)