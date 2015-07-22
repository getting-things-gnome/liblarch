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

import unittest
from liblarch.treenode import _Node
from liblarch.tree import MainTree
from liblarch.filters_bank import FiltersBank
from liblarch.filteredtree import FilteredTree


class TestFilteredTree(unittest.TestCase):
    def setUp(self):
        self.added_nodes = 0
        self.deleted_nodes = 0
        self.tree = MainTree()
        self.filtersbank = FiltersBank(self.tree)
        self.filtered_tree = FilteredTree(self.tree, self.filtersbank)
        self.tree.add_node(_Node(node_id="apple"))
        self.tree.add_node(_Node(node_id="google"))

        self.filtered_tree.set_callback('deleted', self.deleted)
        self.filtered_tree.set_callback('added', self.added)

    def search_filter(self, node, parameters):
        return node.get_id() == parameters['node_id']

    def true_filter(self, node):
        return True

    def test_refresh_every_time_with_parameters(self):
        self.filtersbank.add_filter("search_filter", self.search_filter)
        self.assertTrue(self.filtered_tree.is_displayed(node_id="apple"))
        self.assertTrue(self.filtered_tree.is_displayed(node_id="apple"))

        self.filtered_tree.apply_filter("search_filter",
                                        parameters={'node_id': 'apple'})
        self.assertTrue(self.filtered_tree.is_displayed(node_id="apple"))
        self.assertFalse(self.filtered_tree.is_displayed(node_id="google"))

        # Due to self.refilter() implementation, all nodes are deleted
        # at first and then only those satisfying the filter are added back.
        self.assertEqual(2, self.deleted_nodes)
        self.assertEqual(1, self.added_nodes)

        self.reset_counters()

        self.filtered_tree.apply_filter("search_filter",
                                        parameters={'node_id': 'google'})
        self.assertFalse(self.filtered_tree.is_displayed(node_id="apple"))
        self.assertTrue(self.filtered_tree.is_displayed(node_id="google"))

        self.assertEqual(1, self.deleted_nodes)
        self.assertEqual(1, self.added_nodes)

    def test_refresh_only_with_new_filter(self):
        self.filtersbank.add_filter("true_filter", self.true_filter)

        self.reset_counters()

        self.filtered_tree.apply_filter("true_filter")

        self.assertEqual(2, self.deleted_nodes)
        self.assertEqual(2, self.added_nodes)

        self.reset_counters()

        self.filtered_tree.apply_filter("true_filter")

        self.assertEqual(0, self.deleted_nodes)
        self.assertEqual(0, self.added_nodes)

    def added(self, node_id, path):
        self.added_nodes += 1

    def deleted(self, node_id, path):
        self.deleted_nodes += 1

    def reset_counters(self):
        self.added_nodes, self.deleted_nodes = 0, 0
