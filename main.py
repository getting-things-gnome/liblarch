#!/usr/bin/python
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

import gtk

from liblarch import Tree
from liblarch import TreeNode
from liblarch_gtk import TreeView

import os
import uuid
import sys
from random import randint, choice, shuffle
import re
import logging
from time import sleep, time
import threading
import gobject

# Constants
LOAD_MANY_TASKS_COUNT = 1000
ADD_MANY_TASKS_TO_EXISTING_TASKS = True
SLEEP_BETWEEN_TASKS = 0

# Useful for experimenting with the tree
BACKUP_OPERATIONS = False

def random_task_title_on_id(t_id):
    try:
        return 'Task %5d' % int(t_id)
    except ValueError:
        return 'Task %5s' % t_id

# Generate title in different ways
random_task_title = random_task_title_on_id

MAX_FILE_ID = 0

def save_backup(fun):
    def _save_backup(*args, **kwargs):
        global MAX_FILE_ID 

        self = args[0]

        file_name = "operation_%03d.bak" % MAX_FILE_ID
        while os.path.exists(file_name):
            MAX_FILE_ID += 1
            file_name = "operation_%03d.bak" % MAX_FILE_ID

        stdout = sys.stdout
        stderr = sys.stderr
        output = open(file_name, "w", 0)

        sys.stdout = output
        sys.stderr = output

        print "Tree before operation"
        self.print_tree()
        print
        print "Operation '%s':" % (fun.__name__)

        res = fun(*args, **kwargs)

        print "Tree after operation"
        self.print_tree()

        sys.stdout = stdout
        sys.stderr = stderr

        output.close()

        # Print the log
        output = open(file_name, "r")
        print output.read()
        output.close()

        return res
    
    if BACKUP_OPERATIONS:
        return _save_backup
    else:
        return fun

MAX_ID = 0

def random_id():
    global MAX_ID

    MAX_ID += 1
    return str(MAX_ID)

class TaskNode(TreeNode):

    def __init__(self, tid, label,viewtree):
        TreeNode.__init__(self, tid)
        self.label = label
        self.tid = tid
        self.vt = viewtree

    def get_label(self):
        return "%s (%s children)" % (self.label, self.vt.node_n_children(self.tid,recursive=True))

class Backend(threading.Thread):
    def __init__(self, backend_id, finish_event, delay, tree):
        super(Backend, self).__init__()

        self.backend_id = backend_id
        self.delay = delay  
        self.tree = tree
        self.finish_event = finish_event

    def run(self):
        counter = 0
        parent_id = None
        while not self.finish_event.wait(self.delay):
            task_id = self.backend_id + "_" + str(counter)
            title = task_id
            self.tree.add_node(TaskNode(task_id, title), parent_id,self.view_tree)
            parent_id = task_id

            # Delete some tasks
            for i in range(randint(3,10)):
                delete_id = str(choice([1,3,5]))+"sec_"+str(randint(0, 2*counter))
                print self.backend_id + " deleting " + delete_id
                self.tree.del_node(delete_id)
            counter += 1

        print self.backend_id + " --- finish"

class LiblarchDemo:
    """ Shows a simple GUI demo of liblarch usage
    with several functions for adding tasks """

    def _build_tree_view(self):
        self.tree = Tree()
        self.tree.add_filter("even",self.even_filter)
        self.tree.add_filter("odd",self.odd_filter)
        self.tree.add_filter("flat",self.flat_filter,{"flat": True})
        self.tree.add_filter("leaf",self.leaf_filter)
        self.view_tree = self.tree.get_viewtree()
        self.mod_counter = 0
        
        self.view_tree.register_cllbck('node-added-inview',self._update_title)
        self.view_tree.register_cllbck('node-modified-inview',self._modified_count)
        self.view_tree.register_cllbck('node-deleted-inview',self._update_title)

        desc = {}

        col_name = 'label'
        col = {}
        col['title'] = "Title"
        col['value'] = [str, self.task_label_column]
        col['expandable'] = True
        col['resizable'] = True
        col['sorting'] = 'label'
        col['order'] = 0
        desc[col_name] = col

        tree_view = TreeView(self.view_tree, desc)

        # Polish TreeView
        def on_row_activate(sender,a,b):
            print "Selected nodes are: %s" %str(tree_view.get_selected_nodes())

        tree_view.set_dnd_name('liblarch-demo/liblarch_widget')
        tree_view.set_multiple_selection(True)

        tree_view.set_property("enable-tree-lines", True)
        tree_view.connect('row-activated', on_row_activate)

        return tree_view
        
    def even_filter(self,node):
        if node.get_id().isdigit():
            return int(node.get_id())%2 == 0
        else:
            return False
    
    def odd_filter(self,node):
        return not self.even_filter(node)
        
    def flat_filter(self,node,parameters=None):
        return True
        
    def leaf_filter(self,node):
        return not node.has_child()
        
    def _modified_count(self,nid,path):
#        print "Node %s has been modified" %nid
        self.mod_counter += 1
        
    def _update_title(self,sender,nid):
        count = self.view_tree.get_n_nodes()
        if count == LOAD_MANY_TASKS_COUNT and self.start_time > 0:
            stop_time = time() - self.start_time
            print "Time to load %s tasks: %s" %(LOAD_MANY_TASKS_COUNT,stop_time)
#        if count > 0:
            mean = self.mod_counter * 1.0 / count
            print "%s modified signals were received (%s per task)" %(self.mod_counter, mean)     
        self.window.set_title('Liblarch demo: %s nodes' %count)
        

    def __init__(self):
        self.window = gtk.Window()
        self.window.set_size_request(640, 480)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_border_width(10)
        self.window.set_title('Liblarch demo')
        self.window.connect('destroy', self.finish)

        self.liblarch_widget = self._build_tree_view()
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.add_with_viewport(self.liblarch_widget)
        
        self.start_time = 0

        # Buttons 
        action_panel = gtk.HBox()
        action_panel.set_spacing(5)

        button_desc = [('_Add a Task', self.add_task), 
            ('_Delete a Task', self.delete_task),
            ('_Print Tree', self.print_tree),
            ('_Print FT', self.print_ft),
            ('_Load many Tasks', self.many_tasks),
            ('_Quit', self.finish)]

        for name, callback in button_desc:
            button = gtk.Button(name)
            button.connect('clicked', callback)
            action_panel.pack_start(button)
            
        filter_panel= gtk.HBox()
        filter_panel.set_spacing(5)
            
        for name in self.tree.list_filters():
            button = gtk.ToggleButton("%s filter"%name)
            button.connect('toggled',self.apply_filter,name)
            filter_panel.pack_start(button)

        # Use cases
        usecases_vbox = gtk.VBox()
        usecase_box = None
        usecase_order = 0
        usecase_order_max = 3

        button_desc = [('_Tree high 3', self.tree_high_3),
            ('Tree high 3 backwards', self.tree_high_3_backwards),
            ('Load from file', self.load_from_file),
            ('Delete DFXBCAE', self.delete_magic),
            ('Delete backwards', self.delete_backwards),
            ('Delete randomly', self.delete_random),
            ('Change task', self.change_task),
            ('_Backend use case', self.backends),
            ]

        for name, callback in button_desc:
            if usecase_order <= 0:
                if usecase_box is not None:
                    usecases_vbox.pack_start(usecase_box, False, True)
                usecase_box = gtk.HBox()
                usecase_box.set_spacing(5)

            button = gtk.Button(name)
            button.connect('clicked', callback)
            usecase_box.pack_start(button)

            usecase_order = (usecase_order + 1) % usecase_order_max

        usecases_vbox.pack_start(usecase_box, False, True)
        usecase_panel = gtk.Expander('Use cases')
        usecase_panel.set_expanded(True)
        usecase_panel.add(usecases_vbox)

        # Show it
        vbox = gtk.VBox()
        vbox.pack_start(action_panel, False, True, 10)
        vbox.pack_start(filter_panel, False, True, 10)
        vbox.pack_start(scrolled_window)
        vbox.pack_start(usecase_panel, False, True, 10)

        self.window.add(vbox)
        self.window.show_all()

        self.should_finish = threading.Event()

    def task_label_column(self, node):
        newlabel = node.get_label()
        return newlabel

    def print_tree(self, widget=None):
        print 
        print "=" * 20, "Tree", "=" * 20
        self.tree.get_main_view().print_tree()
        print "=" * 46
        print

    def print_ft(self, widget=None):
        print 
        self.view_tree.print_tree()
        print
    
    @save_backup
    def add_task(self, widget):
        """ Add a new task. If a task is selected,
        the new task is added as its child """
        selected = self.liblarch_widget.get_selected_nodes()

        t_id = random_id()
        t_title = random_task_title(t_id)
        task = TaskNode(t_id, t_title,self.view_tree)

        if len(selected) == 1:
            # Adding a subchild
            parent = selected[0]
            self.tree.add_node(task, parent_id = parent)
            print 'Added sub-task "%s" (%s) for %s' % (t_title, t_id, parent)
        else:
            # Adding as a new child
            self.tree.add_node(task)
            for parent_id in selected:
                task.add_parent(parent_id)
            print 'Added task "%s" (%s)' % (t_title, t_id)
            
    def apply_filter(self,widget,param):
        print "applying filter: %s" %param
        if param in self.view_tree.list_applied_filters():
            self.view_tree.unapply_filter(param)
        else:
            self.view_tree.apply_filter(param)

    @save_backup
    def tree_high_3(self, widget):
        ''' We add the leaf nodes before the root, in order to test
        if it works fine even in this configuration'''
        print 'Adding a tree of height 3'

        selected = self.liblarch_widget.get_selected_nodes()

        if len(selected) == 1:
            parent = selected[0]
        else:
            parent = None
            
        t_id = random_id()
        t_title = random_task_title(t_id)
        roottask = TaskNode(t_id, t_title,self.view_tree)
        local_parent = t_id

        for i in range(2):
            t_id = random_id()
            t_title = random_task_title(t_id)
            task = TaskNode(t_id, t_title,self.view_tree)

            self.tree.add_node(task, parent_id = local_parent)

            # Task becomes a parent for new task
            local_parent = t_id
            
        self.tree.add_node(roottask, parent_id = parent)

    @save_backup
    def tree_high_3_backwards(self, widget):
        print 'Adding a tree of height 3 backwards'

        selected = self.liblarch_widget.get_selected_nodes()

        if len(selected) == 1:
            parent = selected[0]
        else:
            parent = None

        tasks = []
        relationships = []
        for i in range(3):
            t_id = random_id()
            t_title = random_task_title(t_id)
            task = TaskNode(t_id, t_title,self.view_tree)

            tasks.append((t_id, task))

            if parent is not None:
                relationships.append((parent, t_id))

            parent = t_id

        # Relationships can come in any order, e.g. reversed
        relationships = reversed(relationships)

        for t_id, task in tasks:
            print "Adding task to tree:", t_id, task
            self.tree.add_node(task)
            print "="*50

        for parent, child in relationships:
            print "New relationship: ", parent, "with", child
            parent_node = self.tree.get_node(parent)
            parent_node.add_child(child)
            print "="*50

        print

    @save_backup
    def delete_task(self, widget, order='normal'):
        print 'Deleting a task'
        selected = self.liblarch_widget.get_selected_nodes()

        print 'Order: %s' % order

        if   order == 'normal':
            ordered_nodes = selected
        elif order == 'backward':
            ordered_nodes = reversed(selected)
        elif order == 'random':
            ordered_nodes = selected
            shuffle(ordered_nodes)
            # Replace iterator for a list => 
            # we want to see the order in logs and the performance is not important
            ordered_nodes = [node for node in ordered_nodes]
        elif order == 'magic-combination':
            # testing a special case from examples/test_suite
            ordered_nodes = ['D', 'F', 'X', 'B', 'C', 'A', 'E']
        else:
            Log.error('Unknown order, skipping...')
            return

        print "Tasks should be removed in this order:", ordered_nodes

        for node_id in ordered_nodes:
            self.tree.del_node(node_id)
            print 'Removed node %s' % node_id

        self.print_tree(None)

    def delete_backwards(self, widget):
        """ Delete task backward """
        self.delete_task(widget, order='backward')

    def delete_random(self, widget):
        """ Delete tasks in random order """
        self.delete_task(widget, order='random')

    def delete_magic(self, widget):
        self.delete_task(widget, order='magic-combination')

    def change_task(self, widget):
        view = self.tree.get_main_view()
        for node_id in self.liblarch_widget.get_selected_nodes():
            node = self.tree.get_node(node_id)
            node.label = "Ahoj"
            node.modified()

    def backends(self, widget):
        print "Backends...."
        Backend('1sec', self.should_finish, 1, self.tree).start()
        Backend('3sec', self.should_finish, 3, self.tree).start()
        Backend('5sec', self.should_finish, 5, self.tree).start()
        widget.set_sensitive(False)


    def many_tasks(self, widget):
        self.start_time = time()
        def _many_tasks():
            tasks_ids = []
            prefix = randint(1, 1000)* 100000
            for i in range(LOAD_MANY_TASKS_COUNT):
                t_id = str(prefix + i)
                t_title = t_id
                task = TaskNode(t_id, t_title,self.view_tree)

                # There is 25 % chance to adding as a sub_task
                if tasks_ids != [] and randint(0, 100) < 90:
                    parent = choice(tasks_ids)
                    self.tree.add_node(task, parent_id = parent)
                else:
                    self.tree.add_node(task)

                tasks_ids.append(t_id)

                # Sleep 0.01 second to create illusion of real tasks
                sleep(SLEEP_BETWEEN_TASKS)

            print "end of _many_tasks thread"
        t = threading.Thread(target=_many_tasks)
        t.start()

    def load_from_file(self, widget):
        dialog = gtk.FileChooserDialog("Open..", self.window, 
            gtk.FILE_CHOOSER_ACTION_OPEN, 
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            file_name = dialog.get_filename()
        else:
            file_name = None
        dialog.destroy()

        if file_name is None:
            return

        log = open(file_name, 'r').read()

        m = re.match('\s*Tree before operation\s+=+\s+Tree\s+=+\s+(.*?)=+', log, re.UNICODE | re.DOTALL)
        if m:
            treelines = m.group(1)
            items = [(len(line) - len(line.lstrip()), line.strip()) for line in treelines.splitlines()]
            # Filter "root" item and decrease level
            items = [(level, name) for level, name in items[1:]]

            # The "root" items should be at level 0, adjust level to that
            min_level = min(level for level, name in items)
            items = [(level-min_level, name) for level, name in items]

            nodes = list(set([name for level, name in items]))

            relationships = []
            parent_level = { -1: None }

            for level, name in items:
                parent = parent_level[level - 1]
                relationships.append((parent, name))

                for key in list(parent_level.keys()):
                    if key > level:
                        del parent_level[key]

                parent_level[level] = name

            print "Nodes to add:", nodes
            print "Relationships:", "\n".join(str(r) for r in relationships)
            print

            for node_id in nodes:
                task = TaskNode(node_id, random_task_title(node_id),self.view_tree)
                self.tree.add_node(task)

            for parent, child in relationships:
                parent_node = self.tree.get_node(parent)
                parent_node.add_child(child)
        else:
            print "Not matched"
            print "Log: ", log

    def finish(self, widget):
        self.should_finish.set()
        gtk.main_quit()

    def run(self):
        gtk.main()


if __name__ == "__main__":
    gobject.threads_init()
    app = LiblarchDemo()
    app.run()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
