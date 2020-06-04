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

setup(
    version='3.0.1',
    url='https://wiki.gnome.org/Projects/liblarch',
    author='Lionel Dricot & Izidor Matušov',
    author_email='gtg-contributors@lists.launchpad.net',
    license='LGPLv3',
    name='liblarch',
    packages=['liblarch', 'liblarch_gtk'],
    description=(
        'LibLarch is a python library built to easily handle '
        'data structures such as lists, trees and directed acyclic graphs '
        'and represent them as a GTK TreeWidget or in other forms.'
    ),
)
