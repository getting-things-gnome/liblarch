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

"""
filters_bank stores all of GTG's filters in centralized place
"""


class Filter(object):
    def __init__(self, func, req):
        self.func = func
        self.dic = {}
        self.tree = req

    def set_parameters(self, dic):
        if dic:
            self.dic = dic

    def is_displayed(self, node_id):
        if self.tree.has_node(node_id):
            task = self.tree.get_node(node_id)
        else:
            return False

        if self.dic:
            value = self.func(task, parameters=self.dic)
        else:
            value = self.func(task)

        if 'negate' in self.dic and self.dic['negate']:
            value = not value

        return value

    def get_parameters(self, param):
        return self.dic.get(param, None)

    def is_flat(self):
        """ Should be the final list flat """
        return self.get_parameters('flat')


class FiltersBank(object):
    """
    Stores filter objects in a centralized place.
    """

    def __init__(self, tree):
        """
        Create several stock filters:

        workview - Tasks that are active, workable, and started
        active - Tasks of status Active
        closed - Tasks of status closed or dismissed
        notag - Tasks with no tags
        """
        self.tree = tree
        self.available_filters = {}
        self.custom_filters = {}

    ##########################################

    def get_filter(self, filter_name):
        """ Get the filter object for a given name """
        if filter_name in self.available_filters:
            return self.available_filters[filter_name]
        elif filter_name in self.custom_filters:
            return self.custom_filters[filter_name]
        else:
            return None

    def has_filter(self, filter_name):
        return filter_name in self.available_filters \
            or filter_name in self.custom_filters

    def list_filters(self):
        """ List, by name, all available filters """
        liste = list(self.available_filters.keys())
        liste += list(self.custom_filters.keys())
        return liste

    def add_filter(self, filter_name, filter_func, parameters=None):
        """
        Adds a filter to the filter bank
        Return True if the filter was added
        Return False if the filter_name was already in the bank
        """
        if filter_name not in self.list_filters():
            if filter_name.startswith('!'):
                filter_name = filter_name[1:]
            else:
                filter_obj = Filter(filter_func, self.tree)
                filter_obj.set_parameters(parameters)
            self.custom_filters[filter_name] = filter_obj
            return True
        else:
            return False

    def remove_filter(self, filter_name):
        """
        Remove a filter from the bank.
        Only custom filters that were added here can be removed
        Return False if the filter was not removed
        """
        if filter_name not in self.available_filters:
            if filter_name in self.custom_filters:
                self.custom_filters.pop(filter_name)
                return True
            else:
                return False
        else:
            return False
