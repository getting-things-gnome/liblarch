#!/usr/bin/python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Liblarch - a library to handle directed acyclic graphs
# Copyright (c) 2011-2012 - Lionel Dricot & Izidor Matušov
#
# This code is based on a part of Getting Things GNOME! code published
# under GNU GPLv3 - https://launchpad.net/gtg
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

import pstats
p = pstats.Stats('liblarch.prof')
p.strip_dirs().sort_stats("cumulative").print_stats(20)
p.strip_dirs().sort_stats("time").print_stats(20)
p.strip_dirs().sort_stats("file").print_stats(20)
p.print_callers('update_task')
