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

from gi.repository import Gtk, GObject

class TreeModel(Gtk.TreeStore):
    """ Local copy of showed tree """

    def __init__(self, tree, types):
        """ Initializes parent and create list of columns. The first colum
        is node_id of node """
        
        self.count = 0
        self.count2 = 0

        self.types = [[str, lambda node: node.get_id()]] + types
        only_types = [python_type for python_type, access_method in self.types]

        super(TreeModel, self).__init__(*only_types)
        self.cache_paths = {}
        self.cache_position = {}
        self.tree = tree

    def set_column_function(self, column_num, column_func):
        """ Replace function for generating certain column.

        Original use case was changing method of generating background
        color during runtime - background by tags or due date """

        if column_num < len(self.types):
            self.types[column_num][1] = column_func
            return True
        else:
            return False

    def connect_model(self):
        """ Register "signals", callbacks from liblarch.
        
        Also asks for the current status by providing add_task callback.
        We are able to connect to liblarch tree on the fly. """

        self.tree.register_cllbck('node-added-inview',self.add_task)
        self.tree.register_cllbck('node-deleted-inview',self.remove_task)
        self.tree.register_cllbck('node-modified-inview',self.update_task)
        self.tree.register_cllbck('node-children-reordered',self.reorder_nodes)

        # Request the current state
        self.tree.get_current_state()

    def my_get_iter(self, path):
        """ Because we sort the TreeStore, paths in the treestore are
        not the same as paths in the FilteredTree. We do the  conversion here.
        We receive a Liblarch path as argument and return a Gtk.TreeIter"""
        #The function is recursive. We take iter for path (A,B,C) in cache.
        #If there is not, we take iter for path (A,B) and try to find C.
        if path == ():
            return None
        nid = str(path[-1])
        self.count += 1
        #We try to use the cache
        iter = self.cache_paths.get(path,None)
        toreturn = None
        if iter and self.iter_is_valid(iter) and nid == self.get_value(iter,0):
            self.count2 += 1
            toreturn = iter
        else:
            root = self.my_get_iter(path[:-1])
            #This is a small ad-hoc optimisation.
            #Instead of going through all the children nodes
            #We go directly at the last known position.
            pos = self.cache_position.get(path,None)
            if pos:
                iter = self.iter_nth_child(root,pos)
                if iter and self.get_value(iter,0) == nid:
                    toreturn = iter
            if not toreturn:
                if root:
                    iter = self.iter_children(root)
                else:
                    iter = self.get_iter_first()
                while iter and self.get_value(iter,0) != nid:
                    iter = self.iter_next(iter)
            self.cache_paths[path] = iter
            toreturn = iter
#        print "%s / %s" %(self.count2,self.count)
#        print "my_get_iter %s : %s" %(nid,self.get_string_from_iter(toreturn))
        return toreturn

    def print_tree(self):
        """ Print TreeStore as Tree into console """

        def push_to_stack(stack, level, iterator):
            """ Macro which adds a new element into stack if it is possible """
            if iterator is not None:
                stack.append((level, iterator))

        stack = []
        push_to_stack(stack, 0, self.get_iter_first())

        print("+"*50)
        print("Treemodel print_tree: ")
        while stack != []:
            level, iterator = stack.pop()

            print("=>"*level, self.get_value(iterator, 0))

            push_to_stack(stack, level, self.iter_next(iterator))
            push_to_stack(stack, level+1, self.iter_children(iterator))
        print("+"*50)

### INTERFACE TO LIBLARCH #####################################################

    def add_task(self, node_id, path):
        """ Add new instance of node_id to position described at path.

        @param node_id: identification of task
        @param path: identification of position
        """
        node = self.tree.get_node(node_id)

        # Build a new row
        row = []
        for python_type, access_method in self.types:
            value = access_method(node)
            row.append(value)

        # Find position to add task
        iter_path = path[:-1]

        iterator = self.my_get_iter(iter_path)
        self.cache_position[path] = self.iter_n_children(iterator)
        it = self.insert(iterator, -1, row)
        
        # Show the new task if possible
#        self.row_has_child_toggled(self.get_path(it), it)

    def remove_task(self, node_id, path):
        """ Remove instance of node.

        @param node_id: identification of task
        @param path: identification of position
        """
        it = self.my_get_iter(path)
        if not it:
            raise Exception("Trying to remove node %s with no iterator"%node_id)
        actual_node_id = self.get_value(it, 0)
        assert actual_node_id == node_id
        self.remove(it)
        self.cache_position.pop(path)

    def update_task(self, node_id, path):
        """ Update instance of node by rebuilding the row.

        @param node_id: identification of task
        @param path: identification of position
        """
        #We cannot assume that the node is in the tree because
        #update is asynchronus
        #Also, we should consider that missing an update is not critical
        #and ignoring the case where there is no iterator
        if self.tree.is_displayed(node_id):
            node = self.tree.get_node(node_id)
            #That call to my_get_iter is really slow!
            iterator = self.my_get_iter(path)
        
            if iterator:
                for column_num, (python_type, access_method) in enumerate(self.types):
                    value = access_method(node)
                    if value is not None:
                        self.set_value(iterator, column_num, value)

    def reorder_nodes(self, node_id, path, neworder):
        """ Reorder nodes.
        
        This is deprecated signal. In the past it was useful for reordering
        showed nodes of tree. It was possible to delete just the last
        element and therefore every element must be moved to the last position
        and then deleted.

        @param node_id: identification of root node
        @param path: identification of poistion of root node
        @param neworder: new order of children of root node
        """

        if path is not None:
            it = self.my_get_iter(path)
        else:
            it = None
        self.reorder(it, neworder)
        self.print_tree()
