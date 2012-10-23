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
# ---------------------------------------------------------------------------

class ViewCount:
    def __init__(self,tree,fbank, name = None, refresh = True):
        self.initialized = False
        self.ncount = {}
        self.tree = tree
        self.tree.register_callback("node-added", self.__modify)
        self.tree.register_callback("node-modified", self.__modify)
        self.tree.register_callback("node-deleted", self.__delete)
        
        self.fbank = fbank
        self.name = name
        
        self.applied_filters = []
        self.nodes = []
        self.cllbcks = []
        
        if refresh:
            self.__refresh()
                
    def __refresh(self):
        for node in self.tree.get_all_nodes():
            self.__modify(node)
        self.initialized = True
    
    def apply_filter(self,filter_name,refresh=True):
        if self.fbank.has_filter(filter_name):
            if filter_name not in self.applied_filters:
                self.applied_filters.append(filter_name)
                if refresh:
                    #If we are not initialized, we need to refresh with all existing nodes
                    if self.initialized:
                        for n in list(self.nodes):
                            self.__modify(n)
                    else:
                        self.__refresh()
        else:
            #FIXME: raise proper error
            print "There's no filter called %s" %filter_name
            
    def unapply_filter(self,filter_name):
        if filter_name in self.applied_filters:
            self.applied_filters.remove(filter_name)
            for node in self.tree.get_all_nodes():
                self.__modify(node)
    
    #there's only one callback: "modified"
    def register_cllbck(self, func):
        if func not in self.cllbcks:
            self.cllbcks.append(func)
            
    def unregister_cllbck(self,func):
        if func in self.cllbacks:
            self.cllbacks.remove(func)
    
    def get_n_nodes(self):
        return len(self.nodes)
        
    #Allow external update of a given node
    def modify(self,nid):
        self.__modify(nid)
        
    def __modify(self,nid):
        displayed = True
        for filtname in self.applied_filters:
            filt = self.fbank.get_filter(filtname)
            displayed &= filt.is_displayed(nid)
        if displayed:
            self.__add(nid)
        else:
            self.__delete(nid)
        

    
    def __delete(self,nid):
        if nid in self.nodes:
#            print "node %s removed from viewcount %s"%(nid,self.name)
            self.nodes.remove(nid)
            self.__callback()
            
    def __add(self,nid):
        if nid not in self.nodes:
#            print "node %s added to viewcount %s"%(nid,self.name)
            self.nodes.append(nid)
            self.__callback()
        
        
    def __callback(self):
        for c in self.cllbcks:
            c()
