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

#API version of liblarch. 
#Your application is compatible if the major version number match liblarch's one
#and if your minor version number is inferior to liblarch's one.
#
#The minor number is incremented when a method is added to the API
#The major number is incremented if an existing method is removed or modified
api="1.1"

def is_compatible(request):
    major,minor=request.split(".")
    current_ma,current_mi=api.split(".")
    return (major == current_ma and minor <= current_mi)
    
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

# There should be two classes: for static and for dynamic mode
# There are many conditions, and also we would prevent unallowed modes
class ViewTree:
    def __init__(self, maininterface, maintree, filters_bank,\
                                name = None,
                                             refresh = True, static = False):
        """A ViewTree is the interface that should be used to display Tree(s).

           In static mode, FilteredTree layer is not created. (There is no need)

           We connect to MainTree or FilteredTree to get informed about changes.
           If FilteredTree is used, it is connected to MainTree to handle changes
           and then send id to ViewTree if it applies.

           @param maintree: a Tree object, cointaining all the nodes
           @param filters_bank: a FiltersBank object. Filters can be added
                                dinamically to that.
           @param refresh: if True, this ViewTree is automatically refreshed
                           after applying a filter.
           @param static: if True, this is the view of the complete maintree.
                           Filters cannot be added to such a view.
        """
        self.maininterface = maininterface
        self.__maintree = maintree
        self.__cllbcks = {}
        self.__fbank = filters_bank
        self.static = static

        if self.static:
            self._tree = self.__maintree
            self.__ft = None
            self.__maintree.register_callback('node-added', \
                        functools.partial(self.__emit, 'node-added'))
            self.__maintree.register_callback('node-deleted', \
                        functools.partial(self.__emit, 'node-deleted'))
            self.__maintree.register_callback('node-modified', \
                        functools.partial(self.__emit, 'node-modified'))
        else:
            self.__ft = FilteredTree(maintree, filters_bank, name = name, refresh = refresh)
            self._tree = self.__ft
            self.__ft.set_callback('added', \
                        functools.partial(self.__emit, 'node-added-inview'))
            self.__ft.set_callback('deleted', \
                        functools.partial(self.__emit, 'node-deleted-inview'))
            self.__ft.set_callback('modified', \
                        functools.partial(self.__emit, 'node-modified-inview'))
            self.__ft.set_callback('reordered', \
                        functools.partial(self.__emit, 'node-children-reordered'))
                        
    def queue_action(self, node_id,func,param=None):
        self.__ft.set_callback('runonce',func,node_id=node_id,param=param)
        
    def get_basetree(self):
        """ Return Tree object """
        return self.maininterface

    def register_cllbck(self, event, func):
        """ Store function and return unique key which can be used to
        unregister the callback later """

        if not self.__cllbcks.has_key(event):
            self.__cllbcks[event] = {}

        callbacks = self.__cllbcks[event]
        key = 0
        while callbacks.has_key(key):
            key += 1

        callbacks[key] = func
        return key

    def deregister_cllbck(self, event, key):
        """ Remove the callback identifed by key (from register_cllbck) """
        try:
            del self.__cllbcks[event][key]
        except KeyError:
            pass
        
    def __emit(self, event, node_id, path=None, neworder=None):
        """ Handle a new event from MainTree or FilteredTree
        by passing it to other objects, e.g. TreeWidget """
        callbacks = dict(self.__cllbcks.get(event, {}))
#        print "ViewTree __emit for %s" %str(node_id)
        for func in callbacks.itervalues():
#            print "   -> func = %s - %s" %(func,str(path))
            if neworder:
                func(node_id, path, neworder)
            else:
                func(node_id,path)

    def get_node(self, node_id):
        """ Get a node from MainTree """
        return self.__maintree.get_node(node_id)
        
    #FIXME Remove this method from public interface
    def get_root(self):
        return self.__maintree.get_root()

    #FIXME Remove this method from public interface
    def refresh_all(self):
        self.__maintree.refresh_all()

    def get_current_state(self):
        """ Request current state to be send by signals/callbacks.

        This allow LibLarch widget to connect on fly (e.g. after FilteredTree
        is up and has some nodes). """

        if self.static:
            self.__maintree.refresh_all()
        else:
            self.__ft.get_current_state()

    def print_tree(self, string=None):
        """ Print the shown tree, i.e. MainTree or FilteredTree """
        return self._tree.print_tree(string)

    def get_all_nodes(self):
        """ Return list of node_id of displayed nodes """
        return self._tree.get_all_nodes()

    def get_n_nodes(self, withfilters=[], include_transparent=True):
        """ Returns quantity of displayed nodes in this tree

        @withfilters => Additional filters are applied before counting,
        i.e. the currently applied filters are also taken into account

        @inclde_transparent => if it is False, filters which don't have
        the transparent parameters are skipped, not takend into account
        """

        if not self.__ft:
            self.__ft = FilteredTree(self.__maintree, self.__fbank, refresh = True)
        return self.__ft.get_n_nodes(withfilters=withfilters,\
                                    include_transparent=include_transparent)

    def get_node_for_path(self, path):
        """ Convert path to node_id.

        I am not sure what this is for... """
        return self._tree.get_node_for_path(path)

    def get_paths_for_node(self, node_id=None):
        """ If node_id is none, return root path

        *Almost* reverse function to get_node_for_path
        (1 node can have many paths, 1:M)
        """
        return self._tree.get_paths_for_node(node_id)

    # FIXME change pid => parent_id
    def next_node(self, node_id, pid=None):
        """ Return the next node to node_id.

        @parent_id => identify which instance of node_id to work.
        If None, random instance is used """

        return self._tree.next_node(node_id, pid)
        
    def node_has_child(self, node_id):
        """ Has the node at least one child? """
        if self.static:
            return self.__maintree.get_node(node_id).has_child()
        else:
            return self.__ft.node_has_child(node_id)

    def node_all_children(self, node_id=None):
        """ Return children of a node """
        if self.static:
            if not node_id or self.__maintree.has_node(node_id):
                return self.__maintree.get_node(node_id).get_children()
            else:
                return []
        else:
            return self._tree.node_all_children(node_id)

    def node_n_children(self, node_id=None, recursive=False):
        """ Return quantity of children of node_id.
        If node_id is None, use the root node. 
        Every instance of node has the same children"""
        if not self.__ft:
            self.__ft = FilteredTree(self.__maintree, self.__fbank, refresh = True)
        return self.__ft.node_n_children(node_id,recursive)

    def node_nth_child(self, node_id, n):
        """ Return nth child of the node. """
        if self.static:
            if not node_id or node_id == 'root':
                node = self.__maintree.get_root()
            else:
                node = self.__maintree.get_node(node_id)

            if node and node.get_n_children() > n:
                return node.get_nth_child(n)
            else:
                raise ValueError("node %s has less than %s nodes" %(node_id, n))
        else:
            realn = self.__ft.node_n_children(node_id)
            if realn <= n:
                raise ValueError("viewtree has %s nodes, no node %s" %(realn, n))
            return self.__ft.node_nth_child(node_id, n)
        
    def node_has_parent(self, node_id):
        """ Has node parents? Is it child of root? """
        return len(self.node_parents(node_id)) > 0

    def node_parents(self, node_id):
        """ Returns displayed parents of the given node, or [] if there is no 
        parent (such as if the node is a child of the virtual root),
        or if the parent is not displayable.
        Doesn't check wheter node node_id is displayed or not. (we only care about
        parents)
        """
        if self.static:
            return self.__maintree.get_node(node_id).get_parents()
        else:
            return self.__ft.node_parents(node_id)

    def is_displayed(self, node_id):
        """ Is the node displayed? """
        if self.static:
            return self.__maintree.has_node(node_id)
        else:
            return self.__ft.is_displayed(node_id)

####### FILTERS ###############################################################
    def list_applied_filters(self):
        return self.__ft.list_applied_filters()
        
    def apply_filter(self, filter_name, parameters=None, \
                     reset=False, refresh=True):
        """ Applies a new filter to the tree.

        @param filter_name: The name of an already registered filter to apply
        @param parameters: Optional parameters to pass to the filter
        @param reset : optional boolean. Should we remove other filters?
        @param refresh : should we refresh after applying this filter ?
        """
        if self.static:
            raise Exception("WARNING: filters cannot be applied" + \
                            "to a static tree\n")

        self.__ft.apply_filter(filter_name, parameters, reset, refresh)

    def unapply_filter(self,filter_name,refresh=True):
        """ Removes a filter from the tree.

        @param filter_name: The name of filter to remove
        """
        if self.static:
            raise Exception("WARNING: filters cannot be unapplied" +\
                            "from a static tree\n")
        
        self.__ft.unapply_filter(filter_name, refresh)

    def reset_filters(self, refresh=True, transparent_only=False):
        """ Remove all filters currently set on the tree. """
        if self.static:
            raise Exception("WARNING: filters cannot be reset" +\
                            "on a static tree\n")
        else:
             self.__ft.reset_filters(refresh, transparent_only)
