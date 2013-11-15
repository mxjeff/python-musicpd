#! /usr/bin/env python3

from distutils.core import setup

from musicpd import VERSION

DESCRIPTION = """\
An MPD (Music Player Daemon) client library written in pure Python.\
"""


with open('README.txt') as file:
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

LICENSE = """\
Copyright (C) 2008-2010  J. Alexander Treuman <jat@spatialrift.net>
Copyright (C) 2012-2013  Kaliko Jack <kaliko@azylum.org>

python-musicpd is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

python-musicpd is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with python-musicpd.  If not, see <http://www.gnu.org/licenses/>.\
"""


setup(
    name='python-musicpd',
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Kaliko Jack',
    author_email='kaliko@azylum.org',
    url="http://kaliko.me/code/python-musicpd",
    download_url="http://pypi.python.org/pypi/python-musicpd/",
    py_modules=["musicpd"],
    classifiers=CLASSIFIERS,
    license=LICENSE,
    keywords=["mpd"],
    platforms=["Independant"],
)


# vim: set expandtab shiftwidth=4 softtabstop=4 textwidth=79:
