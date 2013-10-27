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

from gi.repository import Gtk, Gdk
from gi.repository import GObject

from liblarch_gtk.treemodel import TreeModel


# Useful for debugging purpose.
# Disabling that will disable the TreeModelSort on top of our TreeModel
ENABLE_SORTING = True
USE_TREEMODELFILTER = False


BRITGHTNESS_CACHE = {}

def brightness(color_str):
    """ Compute brightness of a color on scale 0-1

    Courtesy to
    http://stackoverflow.com/questions/596216/formula-to-determine-brightness-of-rgb-color
    """
    global BRITGHTNESS_CACHE

    if color_str not in BRITGHTNESS_CACHE:
        c = Gdk.color_parse(color_str)
        brightness = (0.2126*c.red + 0.7152*c.green + 0.0722*c.blue)/65535.0
        BRITGHTNESS_CACHE[color_str] = brightness
    return BRITGHTNESS_CACHE[color_str]


class TreeView(Gtk.TreeView):
    """ Widget which display LibLarch FilteredTree.

    This widget extends Gtk.TreeView by several features:
      * Drag'n'Drop support
      * Sorting support
      * separator rows
      * background color of a row
      * selection of multiple rows
    """

    __string_signal__ = (GObject.SignalFlags.RUN_FIRST, None, (str, ))
    __gsignals__ = {'node-expanded' : __string_signal__, \
                    'node-collapsed': __string_signal__, \
                    }

    def __init__(self, tree, description):
        """ Build the widget

        @param  tree - LibLarch FilteredTree
        @param  description - definition of columns.

        Parameters of description dictionary for a column:
          * value => (type of values, function for generating value from a node)
          * renderer => (renderer_attribute, renderer object)

          Optional:
          * order => specify order of column otherwise use natural oreder
          * expandable => is the column expandable?
          * resizable => is the column resizable?
          * visible => is the column visible?
          * title => title of column
          * new_colum => do not create a separate column, just continue with the previous one
                (this can be used to create columns without borders)
          * sorting => allow default sorting on this column
          * sorting_func => use special function for sorting on this func

        Example of columns descriptions:
        description = { 'title': {
                'value': [str, self.task_title_column],
                'renderer': ['markup', Gtk.CellRendererText()],
                'order': 0
            }}
        """
        GObject.GObject.__init__(self)
        self.columns = {}
        self.sort_col = None
        self.sort_order = Gtk.SortType.ASCENDING
        self.bg_color_column = None
        self.separator_func = None

        self.dnd_internal_target = ''
        self.dnd_external_targets = {}
        
        # Sort columns
        self.order_of_column = []
        last = 9999
        for col_name in description:
            desc = description[col_name]
            order = desc.get('order', last)
            last += 1
            self.order_of_column.append((order, col_name))

        types = []
        sorting_func = []
        # Build the first coulumn if user starts with new_colum=False
        col = Gtk.TreeViewColumn()

        # Build columns according to the order
        for col_num, (order_num, col_name) in enumerate(sorted(self.order_of_column), 1):
            desc = description[col_name]
            types.append(desc['value'])

            expand = desc.get('expandable', False)
            resizable = desc.get('resizable', True)
            visible = desc.get('visible', True)

            if 'renderer' in desc:
                rend_attribute, renderer = desc['renderer']
            else:
                rend_attribute = 'markup'
                renderer = Gtk.CellRendererText()

            # If new_colum=False, do not create new column, use the previous one
            # It will create columns without borders
            if desc.get('new_column',True):
                col = Gtk.TreeViewColumn()
                newcol = True
            else:
                newcol = False
            col.set_visible(visible)

            if 'title' in desc:
                col.set_title(desc['title'])

            col.pack_start(renderer, expand=expand)
            col.add_attribute(renderer, rend_attribute, col_num)
            col.set_resizable(resizable)
            col.set_expand(expand)

            # Allow to set background color
            col.set_cell_data_func(renderer, self._celldatafunction)
            
            if newcol:
                self.append_column(col)
            self.columns[col_name] = (col_num, col)

            if ENABLE_SORTING:
                if 'sorting' in desc:
                    # Just allow sorting and use default comparing
                    self.sort_col = desc['sorting']
                    sort_num, sort_col = self.columns[self.sort_col]
                    col.set_sort_column_id(sort_num)

                if 'sorting_func' in desc:
                    # Use special funcion for comparing, e.g. dates
                    sorting_func.append((col_num, col, desc['sorting_func']))

        self.basetree = tree
        # Build the model around LibLarch tree
        self.basetreemodel = TreeModel(tree, types)
        #Applying an intermediate treemodelfilter, for debugging purpose
        if USE_TREEMODELFILTER:
            treemodelfilter = self.basetreemodel.filter_new()
        else:
            treemodelfilter = self.basetreemodel
        # Apply TreeModelSort to be able to sort
        if ENABLE_SORTING:
#            self.treemodel = Gtk.TreeModelSort(treemodelfilter)
            self.treemodel = self.basetreemodel
            for col_num, col, sort_func in sorting_func:
                self.treemodel.set_sort_func(col_num,
                    self._sort_func, sort_func)
                col.set_sort_column_id(col_num)
        else:
            self.treemodel = treemodelfilter

        self.set_model(self.treemodel)

        self.expand_all()
        self.show()
        
        
        self.collapsed_paths = []
        self.connect('row-expanded', self.__emit, 'expanded')
        self.connect('row-collapsed', self.__emit, 'collapsed')
        self.treemodel.connect('row-has-child-toggled', self.on_child_toggled)

    def __emit(self, sender, iter, path, data):
        """ Emit expanded/collapsed signal """
        node_id = self.treemodel.get_value(iter, 0)
        #recreating the path of the collapsed node
        ll_path = ()
        i = 1
        path = path.get_indices()
        while i <= len(path):
            temp_path = Gtk.TreePath(":".join(str(n) for n in path[:i]))
            temp_iter = self.treemodel.get_iter(temp_path)
            ll_path += (self.treemodel.get_value(temp_iter,0),)
            i+=1
        if data == 'expanded':
            self.emit('node-expanded', ll_path)
        elif data == 'collapsed':
            self.emit('node-collapsed', ll_path)

    def on_child_toggled(self, treemodel, path, iter, param=None):
        """ Expand row """
        #is the toggled node in the collapsed paths?
        collapsed = False
        nid = treemodel.get_value(iter,0)
        while iter and not collapsed:
            for c in self.collapsed_paths:
                if c[-1] == nid:
                    collapsed = True
            iter = treemodel.iter_parent(iter)
        if not self.row_expanded(path) and not collapsed:
            self.expand_row(path, True)
            
    def expand_node(self,llpath):
        """ Expand the children of a node. This is not recursive """
        self.collapse_node(llpath,collapsing_method=self.expand_one_row)
        
    def expand_one_row(self,p):
        #We have to set the "open all" parameters
        self.expand_row(p,False)

    def collapse_node(self, llpath,collapsing_method=None):
        """ Hide children of a node
        
        This method is needed for "rember collapsed nodes" feature of GTG.
        Transform node_id into paths and those paths collapse. By default all
        children are expanded (see self.expand_all())
        
        @parameter llpath - LibLarch path to the node. Node_id is extracted
            as the last parameter and then all instances of that node are
            collapsed. For retro-compatibility, we take llpath instead of
            node_id directly"""
        if not collapsing_method:
            collapsing_method = self.collapse_row
        node_id = llpath[-1].strip("'")
        if not node_id:
            raise Exception('Missing node_id in path %s' % str(llpath))

        schedule_next = True
        for path in self.basetree.get_paths_for_node(node_id):
            iter = self.basetreemodel.my_get_iter(path)
            if iter is None:
                continue

            target_path = self.basetreemodel.get_path(iter)
            if self.basetreemodel.get_value(iter, 0) == node_id:
                collapsing_method(target_path)
                self.collapsed_paths.append(path)
                schedule_next = False

        if schedule_next:
            self.basetree.queue_action(node_id, collapsing_method, param=llpath)

    def show(self):
        """ Shows the TreeView and connect basetreemodel to LibLarch """
        Gtk.TreeView.show(self)
        self.basetreemodel.connect_model()

    def get_columns(self):
        """ Return the list of columns name """
        return self.columns.keys()

    def set_main_search_column(self, col_name):
        """ Set search column for GTK integrate search
        This is just wrapper to use internal representation of columns"""
        col_num, col = self.columns[col_name]
        self.set_search_column(col_num)

    def set_expander_column(self, col_name):
        """ Set expander column (that which expands through free space)
        This is just wrapper to use internal representation of columns"""
        col_num, col = self.columns[col_name]
        self.set_property("expander-column", col)

    def set_sort_column(self, col_name, order=Gtk.SortType.ASCENDING):
        """ Select column to sort by it by default """
        if ENABLE_SORTING:
            self.sort_col = col_name
            self.sort_order = order
            col_num, col = self.columns[col_name]
            self.treemodel.set_sort_column_id(col_num, order)

    def get_sort_column(self):
        """ Get sort column """
        if ENABLE_SORTING:
            return self.sort_col, self.sort_order

    def set_col_visible(self, col_name,visible):
        """ Set visiblity of column.
        Allow to hide/show certain column """
        col_num, col = self.columns[col_name]
        col.set_visible(visible)

    def set_col_resizable(self, col_name, resizable):
        """ Allow/forbid column to be resizable """
        col_num, col = self.columns[col_name]
        col.set_resizable(resizable)

    def set_bg_color(self, color_func, color_column):
        """ Set which column and function for generating background color

        Function should be in format func(node, default_color)
        """

        def closure_default_color(func, column):
            """ Set default color to the function.

            Transform function from func(node, default_color) into func(node).
            Default color is computed based on some GTK style magic. """
            style = column.get_tree_view().get_style_context()
            default = style.get_background_color(Gtk.StateFlags.NORMAL).to_color()
            return lambda node: func(node, default)
            
        if self.columns.has_key(color_column):
            self.bg_color_column, column = self.columns[color_column]
            func = closure_default_color(color_func, column)
            self.treemodel.set_column_function(self.bg_color_column, func)
        else:
            raise ValueError("There is no colum %s to use to set color" % \
                color_column)

    def _sort_func(self, model, iter1, iter2, func=None):
        """ Sort two iterators by function which gets node objects.
        This is a simple wrapper which prepares node objects and then
        call comparing function. In other case return default value -1
        """
        node_id_a = model.get_value(iter1, 0)
        node_id_b = model.get_value(iter2, 0)
        if node_id_a and node_id_b and func:
            id, order = self.treemodel.get_sort_column_id()
            node_a = self.basetree.get_node(node_id_a)
            node_b = self.basetree.get_node(node_id_b)
            sort = func(node_a, node_b, order)
        else:
            sort = -1
        return sort

    def _celldatafunction(self, column, cell, model, myiter, user_data):
        """ Determine background color for cell
        
        Requirements: self.bg_color_column must be set
        (see self.set_bg_color())

        Set background color based on a certain column value.
        """
        if self.bg_color_column is None:
            return

        if myiter and model.iter_is_valid(myiter):
            color = model.get_value(myiter, self.bg_color_column)
        else:
            color = None

        if isinstance(cell, Gtk.CellRendererText):
            if color is not None and brightness(color) < 0.5:
                cell.set_property("foreground", '#FFFFFF')
            else:
                # Otherwise unset foreground color
                cell.set_property("foreground-set", False)
       
        cell.set_property("cell-background", color)

    ######### DRAG-N-DROP functions #####################################

    def set_dnd_name(self, dndname):
        """ Sets Drag'n'Drop name and initialize Drag'n'Drop support
        
        If ENABLE_SORTING, drag_drop signal must be handled by this widget."""
        self.dnd_internal_target = dndname
        self.__init_dnd()
        self.connect('drag_data_get', self.on_drag_data_get)
        self.connect('drag_data_received', self.on_drag_data_received)
            

    def set_dnd_external(self, sourcename, func):
        """ Add a new external target and initialize Drag'n'Drop support"""
        i = 1
        while self.dnd_external_targets.has_key(i):
            i += 1
        self.dnd_external_targets[i] = [sourcename, func]
        self.__init_dnd()

    def __init_dnd(self):
        """ Initialize Drag'n'Drop support
        
        Firstly build list of DND targets:
            * name
            * scope - just the same widget / same application
            * id

        Enable DND by calling enable_model_drag_dest(), 
        enable_model-drag_source()

        It didnt use support from Gtk.Widget(drag_source_set(),
        drag_dest_set()). To know difference, look in PyGTK FAQ:
        http://faq.pyGtk.org/index.py?file=faq13.033.htp&req=show
        """
        self.defer_select = False
        
        if self.dnd_internal_target == '':
            error = 'Cannot initialize DND without a valid name\n'
            error += 'Use set_dnd_name() first'
            raise Exception(error)
            
        dnd_targets = [(self.dnd_internal_target, Gtk.TargetFlags.SAME_WIDGET, 0)]
        for target in self.dnd_external_targets:
            name = self.dnd_external_targets[target][0]
            dnd_targets.append((name, Gtk.TargetFlags.SAME_APP, target))
    
        self.enable_model_drag_source( Gdk.ModifierType.BUTTON1_MASK,
            dnd_targets, Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE)

        self.enable_model_drag_dest(\
            dnd_targets, Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE)
    
    def on_drag_data_get(self, treeview, context, selection, info, timestamp):
        """ Extract data from the source of the DnD operation.
        
        Serialize iterators of selected tasks in format 
        <iter>,<iter>,...,<iter> and set it as parameter of DND """

        treeselection = treeview.get_selection()
        model, paths = treeselection.get_selected_rows()
        iters = [model.get_iter(path) for path in paths]
        iter_str = ','.join([model.get_string_from_iter(iter) for iter in iters])
        selection.set(selection.get_target(), 0, iter_str)

    def on_drag_data_received(self, treeview, context, x, y, selection, info,\
                              timestamp):
        """ Handle a drop situation.

        First of all, we need to get id of node which should accept
        all draged nodes as their new children. If there is no node,
        drop to root node.

        Deserialize iterators of dragged nodes (see self.on_drag_data_get())
        Info parameter determines which target was used:
            * info == 0 => internal DND within this TreeView
            * info > 0 => external DND
        
        In case of internal DND we just use Tree.move_node().
        In case of external DND we call function associated with that DND
        set by self.set_dnd_external()
        """
        #TODO: it should be configurable for each TreeView if you want:
        # 0 : no drag-n-drop at all
        # 1 : drag-n-drop move the node
        # 2 : drag-n-drop copy the node 

        model = treeview.get_model()
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            path, position = drop_info
            iter = model.get_iter(path)
            # Must add the task to the parent of the task situated
            # before/after 
            if position == Gtk.TreeViewDropPosition.BEFORE or\
               position == Gtk.TreeViewDropPosition.AFTER:
                # Get sibling parent
                destination_iter = model.iter_parent(iter)
            else:
                # Must add task as a child of the dropped-on iter
                # Get parent
                destination_iter = iter

            if destination_iter:
                destination_tid = model.get_value(destination_iter, 0)
            else:
                #it means we have drag-n-dropped above the first task
                # we should consider the destination as a root then.
                destination_tid = None
        else:
            # Must add the task to the root
            # Parent = root => iter=None
            destination_tid = None

        tree = self.basetree.get_basetree()

        # Get dragged iter as a TaskTreeModel iter
        # If there is no selected task (empty selection.data), 
        # explictly skip handling it (set to empty list)
        data = selection.get_data()
        if data == '':
            iters = []
        else:
            iters = data.split(',')

        dragged_iters = []
        for iter in iters:
            if info == 0:
                try:
                    dragged_iters.append(model.get_iter_from_string(iter))
                except ValueError:
                    #I hate to silently fail but we have no choice.
                    #It means that the iter is not good.
                    #Thanks shitty gtk API for not allowing us to test the string
                    dragged_iter = None

            elif info in self.dnd_external_targets and destination_tid:
                f = self.dnd_external_targets[info][1]

                src_model = context.get_source_widget().get_model()
                dragged_iters.append(src_model.get_iter_from_string(iter))
                
                
        for dragged_iter in dragged_iters:
            if info == 0:
                if dragged_iter and model.iter_is_valid(dragged_iter):
                    dragged_tid = model.get_value(dragged_iter, 0)
                    try:
                        tree.move_node(dragged_tid, new_parent_id=destination_tid)
                    except Exception as e:
                        print('Problem with dragging: %s' % e)
            elif info in self.dnd_external_targets and destination_tid:    
                source = src_model.get_value(dragged_iter,0)
                # Handle external Drag'n'Drop
                f(source, destination_tid)


    ######### Separators support ##############################################
    def _separator_func(self, model, itera, user_data=None):
        """ Call user function to determine if this node is separator """
        if itera and model.iter_is_valid(itera):
            node_id = model.get_value(itera, 0)
            node = self.basetree.get_node(node_id)
            if self.separator_func:
                return self.separator_func(node)
            else:
                return False
        else:
            return False

    def set_row_separator_func(self, func):
        """ Enable support for row separators.

        @param func - function which determines if a node is separator,
            None will disable support for row separators.
        """
        self.separator_func = func
#FIXME
        Gtk.TreeView.set_row_separator_func(self,self._separator_func, None)

    ######### Multiple selection ####################################################
    def get_selected_nodes(self):
        """ Return list of node_id from liblarch for selected nodes """
        # Get the selection in the Gtk.TreeView
        selection = self.get_selection()
        # Get the selection iter
        if selection.count_selected_rows() <= 0:
            ids = []
        else:
            model, paths = selection.get_selected_rows()
            iters = [model.get_iter(path) for path in paths]
            ts  = self.get_model()
            #0 is the column of the tid
            ids = [ts.get_value(iter, 0) for iter in iters]

        return ids

    def set_multiple_selection(self, multiple_selection):
        """ Allow/forbid multiple selection in TreeView """
        # TODO support for dragging multiple rows at the same time
        # See LP #817433

        if multiple_selection:
            selection_type = Gtk.SelectionMode.MULTIPLE
        else:
            selection_type = Gtk.SelectionMode.SINGLE

        self.get_selection().set_mode(selection_type)
