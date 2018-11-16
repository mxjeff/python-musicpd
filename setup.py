#! /usr/bin/env python3
# coding: utf-8

from setuptools import setup

from musicpd import VERSION

DESCRIPTION = """\
An MPD (Music Player Daemon) client library written in pure Python.\
"""


with open('README.rst', encoding='UTF-8') as file:
    LONG_DESCRIPTION = file.read()

CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Topic :: Software Development :: Libraries :: Python Modules",
]


setup(
    name='python-musicpd',
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Kaliko Jack',
    author_email='kaliko@azylum.org',
    url='http://kaliko.me/code/python-musicpd',
    download_url='http://pypi.python.org/pypi/python-musicpd/',
    py_modules=['musicpd'],
    classifiers=CLASSIFIERS,
    license='LGPLv3+',
    keywords=['mpd', 'Music Player Daemon'],
    platforms=['Independant'],
)


# vim: set expandtab shiftwidth=4 softtabstop=4 textwidth=79:
