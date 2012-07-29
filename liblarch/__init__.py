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

import functools

from liblarch.tree import MainTree
from liblarch.treenode import _Node
from liblarch.filteredtree import FilteredTree
from liblarch.filters_bank import FiltersBank
from liblarch.viewtree import ViewTree

# API version of liblarch. 
# Your application is compatible if the major version number match liblarch's
# one and if your minor version number is inferior to liblarch's one.
#
# The major number is incremented if an existing method is removed or modified
# The minor number is incremented when a method is added to the API
API = "1.2"


def is_compatible(request):
    major, minor = [int(i) for i in request.split(".")]
    current_ma, current_mi = [int(i) for i in API.split(".")]
    return major == current_ma and minor <= current_mi
    
class TreeNode(_Node):
    """ The public interface for TreeNode
    """
    def __init__(self, node_id, parent=None):
        _Node.__init__(self,node_id,parent)
        
    def _set_tree(tree):
        print "_set_tree is not part of the API"

class Tree:
    """ A thin wrapper to MainTree that adds filtering capabilities.
    It also provides a few methods to operate complex operation on the
    MainTree (e.g, move_node) """ 

    def __init__(self):
        """ Creates MainTree which wraps and a main view without filters """
        self.__tree = MainTree()
        self.__fbank = FiltersBank(self.__tree)
        self.__views = {}
        self.__views['main'] = ViewTree(self, self.__tree, self.__fbank, static=True)

##### HANDLE NODES ############################################################

    def get_node(self, node_id):
        """ Returns the object of node.
        If the node does not exists, a ValueError is raised. """
        return self.__tree.get_node(node_id)

    def has_node(self, node_id):
        """ Does the node exists in this tree? """
        return self.__tree.has_node(node_id)

    def add_node(self, node, parent_id=None, priority="low"):
        """ Add a node to tree. If parent_id is set, put the node as a child of
        this node, otherwise put it as a child of the root node."""
        self.__tree.add_node(node, parent_id, priority)

    def del_node(self, node_id, recursive=False):
        """ Remove node from tree and return whether it was successful or not """
        return self.__tree.remove_node(node_id, recursive)

    def refresh_node(self, node_id, priority="low"):
        """ Send a request for updating the node """
        self.__tree.modify_node(node_id, priority)

    def refresh_all(self):
        """ Refresh all nodes """
        self.__tree.refresh_all()

    def move_node(self, node_id, new_parent_id=None):
        """ Move the node to a new parent (dismissing all other parents)
        use pid None to move it to the root """
        if self.has_node(node_id):
            node = self.get_node(node_id)
            node.set_parent(new_parent_id)
            toreturn = True
        else:
            toreturn = False

        return toreturn


    def add_parent(self, node_id, new_parent_id=None):
        """ Add the node to a new parent. Return whether operation was
        successful or not. If the node does not exists, return False """

        if self.has_node(node_id):
            node = self.get_node(node_id)
            return node.add_parent(new_parent_id)
        else:
            return False

##### VIEWS ###################################################################
    def get_main_view(self):
        """ Return the special view "main" which is without any filters on it."""
        return self.__views['main']

    def get_viewtree(self, name=None, refresh=True):
        """ Returns a viewtree by the name:
          * a viewtree with that name exists => return it
          * a viewtree with that name does not exist => create a new one and return it
          * name is None => create an anonymous tree (do not remember it)

        If refresh is False, the view is not initialized. This is useful as
        an optimization if you plan to apply a filter.
        """

        if name is not None and self.__views.has_key(name):
            view_tree = self.__views[name]
        else:
            view_tree = ViewTree(self,self.__tree,self.__fbank, name = name, refresh = refresh)
            if name is not None:
                self.__views[name] = view_tree
        return view_tree

##### FILTERS ##################################################################
    def list_filters(self):
        """ Return a list of all available filters by name """
        return self.__fbank.list_filters()

    def add_filter(self, filter_name, filter_func, parameters=None):
        """ Adds a filter to the filter bank.

        @filter_name : name to give to the filter
        @filter_func : the function that will filter the nodes
        @parameters : some default parameters fot that filter
        Return True if the filter was added
        Return False if the filter_name was already in the bank
        """
        return self.__fbank.add_filter(filter_name, filter_func, parameters)

    def remove_filter(self,filter_name):
        """ Remove a filter from the bank. Only custom filters that were 
        added here can be removed. Return False if the filter was not removed.
        """
        return self.__fbank.remove_filter(filter_name)
