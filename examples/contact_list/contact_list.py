# -*- coding: utf-8 -*-
#!/bin/python

#The following code is an example that build a GTK contact-list with liblarch
#If you have some basic PyGTK experience, the code should be straightforward. 

import sys, gtk

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
        
    def get_status(self):
        return self.status
        
    def set_nick(self,nick):
        self.nick = nick
        
    def get_nick(self):
        return self.nick
        
#Each team is also a node
class NodeTeam(TreeNode):
    def __init__(self,node_id):
        TreeNode.__init__(self,node_id)
        #A team cannot have parents. This is arbitrarly done for the purpose
        #of this example.
        self.set_parents_enabled(False)
        
    def get_type(self):
        return "team"
        
    def get_nick(self):
        return self.get_id()
        


class contact_list_window():

    
    def __init__(self):
        #First we do all the GTK stuffs
        # This is not interesting from a liblarch perspective
        self.window = gtk.Window()
        self.window.set_size_request(200, 600)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_border_width(2)
        self.window.set_title('Liblarch contact-list')
        self.window.connect('destroy', self.quit)
        vbox = gtk.VBox()
        #A check button to show/hide offline contacts
        show_offline = gtk.CheckButton("Show offline contacts")
        show_offline.connect("toggled",self.show_offline_contacts)
        vbox.pack_start(show_offline,False, True, 10)
        #The search through contacts
        search = gtk.Entry()
        search.get_buffer().connect("inserted-text",self.search)
        search.get_buffer().connect("deleted-text",self.search)
        vbox.pack_start(search,False, True, 10)
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
        vbox.pack_start(box,False, True, 10)
        
        
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
        
        #the third column is the nickname
        col = {}
        col['value'] = [str, lambda node: node.get_nick()]
        col['visible'] = True
        col['order'] = 2
        columns['nick'] = col
        
        
        return TreeView(self.view,columns)
    
    #This is the "online" filter.
    #It returns the contacts that are busy or online
    #and teams that have at least one contact displayed
    def is_node_online(self,node):
        if node.get_type() == "contact":
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
        #else we apply the "online" filter, showing only online/busy people
        else:
            self.view.apply_filter('online')
        
    def search(self,widget,position,char,nchar=None):
        print "searching for : %s" %widget.get_text()
        
    def quit(self, widget):
        gtk.main_quit()



#We launch the GTK main_loop
if __name__ == "__main__":
#    gobject.threads_init()
    contact_list_window()
    gtk.main()

