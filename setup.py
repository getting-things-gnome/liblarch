#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Liblarch - a library to handle directed acyclic graphs
# Copyright (c) 2011-2012 - Lionel Dricot & Izidor Matušov
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

from distutils.core import setup
import codecs
import os

def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    HERE = os.path.abspath(os.path.dirname(__file__))

    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()

setup(
    version='3.1.0',
    url='https://wiki.gnome.org/Projects/liblarch',
    author='Lionel Dricot & Izidor Matušov',
    author_email='gtg-contributors@lists.launchpad.net',
    license='LGPLv3',
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    name='liblarch',
    packages=['liblarch', 'liblarch_gtk'],
    python_requires=">=3.5",
    keywords = ["gtk", "treeview", "treemodel"],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Topic :: Desktop Environment :: Gnome",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
    ],
    description=(
        'LibLarch is a python library built to easily handle '
        'data structures such as lists, trees and directed acyclic graphs '
        'and represent them as a GTK TreeWidget or in other forms.'
    ),
)
