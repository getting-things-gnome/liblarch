#!/bin/python

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
['joe@dalton.com','busy','Joe Dalton',['daltons','angry']],

]


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
        
    
    def make_contact_list(self):
        return gtk.TreeView()
    
        
    def show_offline_contacts(self,widget):
        print "show offline contact: %s" %widget
        
    def search(self,widget,position,char,nchar=None):
        print "searching for : %s" %widget.get_text()
        
    def quit(self, widget):
        gtk.main_quit()



#We launch the GTK main_loop
if __name__ == "__main__":
#    gobject.threads_init()
    contact_list_window()
    gtk.main()

