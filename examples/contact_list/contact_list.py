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

#The following code is an example that build a GTK contact-list with liblarch
#If you have some basic PyGTK experience, the code should be straightforward. 

import sys, gtk
#for the CellRenderer
import cairo, gobject

#First, we import this liblarch
sys.path.append("../../../liblarch")
from liblarch import Tree, TreeNode
from liblarch_gtk import TreeView

#The contacts (this is a static list for the purpose of the example)
#We have the following:
#1: XMPP address
#2: status: online, busy or offline
#3: Name or nickname
#4: The teams in which the contact is
CONTACTS=[
['me@myself.com','online','Myself',[]],
['ploum@gtg.net','online','Lionel',['gtg','gnome']],
['izidor@gtg.net','busy','Izidor',['gtg','gnome']],
['bertrand@gtg.net','offline','Bertrand',['gtg','on holidays']],
['joe@dalton.com','busy','Joe Dalton',['daltons']],
['jack@dalton.com','offline','Jack Dalton',['daltons']],
['william@dalton.com','offline','William Dalton',['daltons', 'on holidays']],
['averell@dalton.com','online','Averell Dalton',['daltons']],
['guillaume@gnome.org','busy','Guillaume (Ploum)',['gnome']],
['xavier@gnome.org','busy','Navier',['gnome']],
['vincent@gnome.org','busy','Nice Hat',['gnome']]
]


# This is the "Contact" object. 
class NodeContact(TreeNode):
    def __init__(self,node_id):
        self.status = "online"
        self.nick = ""
        TreeNode.__init__(self,node_id)
        #A contact cannot have children node. We disable that
        self.set_children_enabled(False)
        
    def get_type(self):
        return "contact"
        
    def set_status(self,status):
        self.status = status
        self.modified()
        
    def get_status(self):
        return self.status
        
    def set_nick(self,nick):
        self.nick = nick
        self.modified()
        
    def get_nick(self):
        return self.nick
        
    def get_label(self):
        #The label is the nickname in bold followed by the XMPP address (small)
        if self.status == "offline":
            label = "<b><span color='#888'>%s</span></b>" %self.nick
        else:
            label = "<b>%s</b>" %self.nick
        label += " <small><span color='#888'>(%s)</span></small>" %(self.get_id())
        return label
        
#Each team is also a node
class NodeTeam(TreeNode):
    def __init__(self,node_id):
        TreeNode.__init__(self,node_id)
        #A team cannot have parents. This is arbitrarly done for the purpose
        #of this example.
        self.set_parents_enabled(False)
        
    def get_type(self):
        return "team"
        
    def get_label(self):
        return self.get_id()
        
    def get_status(self):
        return None
        


class contact_list_window():

    
    def __init__(self):
        # First we do all the GTK stuff
        # This is not interesting from a liblarch perspective
        self.window = gtk.Window()
        self.window.set_size_request(300, 600)
        self.window.set_border_width(12)
        self.window.set_title('Liblarch contact-list')
        self.window.connect('destroy', self.quit)
        vbox = gtk.VBox()
        vbox.set_spacing(6)
        #A check button to show/hide offline contacts
        show_offline = gtk.CheckButton("Show offline contacts")
        show_offline.connect("toggled",self.show_offline_contacts)
        vbox.pack_start(show_offline, False, True)
        #The search through contacts
        search = gtk.Entry()
        search.set_icon_from_icon_name(0, "search")
        search.get_buffer().connect("inserted-text",self.search)
        search.get_buffer().connect("deleted-text",self.search)
        vbox.pack_start(search, False, True)
        #The contact list, build with liblarch
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.add_with_viewport(self.make_contact_list())
        scrolled_window.set_policy(gtk.POLICY_NEVER,gtk.POLICY_AUTOMATIC)
        vbox.pack_start(scrolled_window)
        #Status
        box = gtk.combo_box_new_text()
        box.append_text("Online")
        box.append_text("Busy")
        box.append_text("Offline")
        box.set_active(0)
        box.connect('changed',self.status_changed)
        vbox.pack_start(box, False, True)
        self.window.add(vbox)
        self.window.show_all()
        
    
    #This is the interesting part on how we use liblarch
    def make_contact_list(self):
    
        ##### LIBLARCH TREE CONSTRUCTION
        #First thing, we create a liblarch tree
        self.tree = Tree()
        #Now, we add each contact *and* each team as nodes of that tree.
        #The team will be the parents of the contact nodes.
        for contact in CONTACTS:
            #We create the node and use the XMPP address as the node_id
            node = NodeContact(contact[0])
            #We add the status and the nickname
            node.set_status(contact[1])
            node.set_nick(contact[2])
            #The contact node is added to the tree
            self.tree.add_node(node)
            #Now, we create the team if it was not done before
            for team_name in contact[3]:
                if not self.tree.has_node(team_name):
                    team_node = NodeTeam(team_name)
                    self.tree.add_node(team_node)
                #now we put the contact under the team
                node.add_parent(team_name)
                #we could also have done
                #team_node.add_child(contact[0])
        
        ###### LIBLARCH VIEW and FILTER
        #Ok, now we have our liblarch tree. What we need is a view.
        self.view = self.tree.get_viewtree()
        #We also create a filter that will allow us to hide offline people
        self.tree.add_filter("online",self.is_node_online)
        self.offline = False
        self.tree.add_filter("search",self.search_filter)
        #And we apply this filter by default
        self.view.apply_filter("online")
        
        ###### LIBLARCH GTK.TreeView
        #And, now, we build our Gtk.TreeView
        #We will build each column of our TreeView
        columns = {}
        #The first column contain the XMPP address but will be hidden
        #But it is still useful for searching
        col = {}
        col['value'] = [str, lambda node: node.get_id()]
        col['visible'] = False
        col['order'] = 0
        columns['XMPP'] = col
        #The second column is the status
        col = {}
        render_tags = CellRendererTags()
        render_tags.set_property('xalign', 0.0)
        col['renderer'] = ['status',render_tags]
        col['value'] = [gobject.TYPE_PYOBJECT,lambda node: node.get_status()]
        col['expandable'] = False
        col['resizable'] = False
        col['order'] = 1
        columns['status'] = col
        #the third column is the nickname
        col = {}
        col['value'] = [str, lambda node: node.get_label()]
        col['visible'] = True
        col['order'] = 2
        columns['nick'] = col
        
        
        return TreeView(self.view,columns)
    
    #This is the "online" filter.
    #It returns the contacts that are busy or online
    #and teams that have at least one contact displayed
    def is_node_online(self,node):
        if node.get_type() == "contact":
            #Always show myself
            if node.get_id() == 'me@myself.com': 
                return True
            status = node.get_status()
            if status == "online" or status == "busy":
                return True
            else:
                return False
        #For the team, we test each contact of that team
        elif node.get_type() == "team":
            tree = node.get_tree()
            for child_id in node.get_children():
                child = tree.get_node(child_id)
                status = child.get_status()
                if status == "online" or status == "busy":
                    return True
            return False
        return True
        
    def show_offline_contacts(self,widget):
        #We should remove the filter to show offline contacts
        if widget.get_active():
            self.view.unapply_filter('online')
            self.offline = True
        #else we apply the "online" filter, showing only online/busy people
        else:
            self.view.apply_filter('online')
            self.offline = False
            
    def status_changed(self,widget):
        new = widget.get_active_text()
        node = self.tree.get_node('me@myself.com')
        if new == 'Busy': node.set_status('busy')
        elif new == 'Offline': node.set_status('offline')
        else: node.set_status('online')
        
    def search(self,widget,position,char,nchar=None):
        search_string = widget.get_text()
        if len(search_string) > 0:
            #First, we remove the old filter
            #note the "refresh=False", because we know we will apply
            #another filter just afterwards
            #We also remove the online filter to search through offline contacts
            if not self.offline:
                self.view.unapply_filter('online',refresh=False)
            self.view.unapply_filter('search',refresh=False)
            self.view.apply_filter('search',parameters={'search':search_string})
        else:
            if not self.offline:
                self.view.apply_filter('online')
            self.view.unapply_filter('search')
        
    def search_filter(self,node,parameters=None):
        string = parameters['search']
        if node.get_type() == "contact":
            if string in node.get_id() or string in node.get_nick():
                return True
            else:
                return False
        else:
            return False
        
    def quit(self, widget):
        gtk.main_quit()


#The following is a custom CellRenderer that will make a coloured circle
#This is aboslutely not needed for liblarch.
#The purpose of using it is to show that liblarch works with 
#complex cellrenderer too
class CellRendererTags(gtk.GenericCellRenderer):
    __gproperties__ = {
        'status': (gobject.TYPE_PYOBJECT, "Status",\
             "Status", gobject.PARAM_READWRITE),
    }

    # Class methods
    def __init__(self): #pylint: disable-msg=W0231
        self.__gobject_init__()
        self.status = None
        self.xpad     = 1
        self.ypad     = 1
        self.PADDING  = 1

    def do_set_property(self, pspec, value):
        if pspec.name == "status":
            self.status = value
        else:
            setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        if pspec.name == "status":
            return self.status
        else:
            return getattr(self, pspec.name)

    def on_render(\
        self, window, widget, background_area, cell_area, expose_area, flags):
        # Drawing context
        cr         = window.cairo_create()
        gdkcontext = gtk.gdk.CairoContext(cr)
        gdkcontext.set_antialias(cairo.ANTIALIAS_NONE)
        # Coordinates of the origin point
        x_align = self.get_property("xalign")
        y_align = self.get_property("yalign")
        rect_x  = cell_area.x
        rect_y  = cell_area.y + int((cell_area.height - 16) * y_align)
        colours = { "online": "#0FDD28", "busy": "#E81110", "offline": "#777"}
        if self.status:
            color = colours[self.status]
            # Draw circle
            radius = 7
            my_color = gtk.gdk.color_parse(color)
            gdkcontext.set_source_color(my_color)
            gdkcontext.arc(rect_x,rect_y+8,radius,90,180)
            gdkcontext.fill()

            # Outer line
            gdkcontext.set_source_rgba(0, 0, 0, 0.20)
            gdkcontext.set_line_width(1.0)
            gdkcontext.arc(rect_x,rect_y+8,radius,90,180)
            gdkcontext.stroke()


    def on_get_size(self, widget, cell_area=None): #pylint: disable-msg=W0613

        if self.status:
            return (self.xpad, self.ypad, self.xpad*2 + 16 +\
                 2*self.PADDING, 16 + 2*self.ypad)
        else:
            return (0,0,0,0)

gobject.type_register(CellRendererTags)
##### End of the cell renderer


#We launch the GTK main_loop
if __name__ == "__main__":
#    gobject.threads_init()
    contact_list_window()
    gtk.main()

