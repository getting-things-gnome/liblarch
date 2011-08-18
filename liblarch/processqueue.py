# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Getting Things Gnome! - a personal organizer for the GNOME desktop
# Copyright (c) 2008-2011 - Lionel Dricot & Bertrand Rousseau
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------


import threading
import gobject

class SyncQueue:
    """ Synchronized queue for processing requests"""

    def __init__(self):
        """ Initialize synchronized queue.

        @param callback - function for processing requests"""
        self._queue = []
        self._vip_queue = []
        self._handler = None
        self._lock = threading.Lock()
        
    def process_queue(self):
        """ Process requests from queue """
        for action in self.process():
            func = action[0]
            func(*action[1:])
#            gobject.idle_add(func,*action[1:])

        # return True to process other requests as well
        return True

    def push(self, *element):
        """ Add a new element to the queue.

        Schedule its processing if it is not already.  
        """
        self._lock.acquire()
#        print "pushing %s in the queue" %str(element)
#        lon = len(self._queue)
#        if lon > 0:
#            print "queue is %s long" %lon
#        if element in self._queue:
#            print "**** double work *** "
        self._queue.append(element)

        if self._handler is None:
            self._handler = gobject.idle_add(self.process_queue)
        self._lock.release()
        
    def priority_push(self, *element):
        """ Add a new element to the queue.

        Schedule its processing if it is not already.  
        vip element are in a priority queue. They will be processed first
        (this comment was actually written in Berlin Airport, after having
        to wait in an economy class queue)"""
        self._lock.acquire()
        self._vip_queue.append(element)

        if self._handler is None:
            self._handler = gobject.idle_add(self.process_queue)
        self._lock.release()

    def process(self):
        """ Return elements to process
        
        At the moment, it returns just one element. In the future more
        elements may be better to return (to speed it up).
        
        If there is no request left, disable processing. """

        self._lock.acquire()
        if len(self._vip_queue) > 0:
            toreturn = [self._vip_queue.pop(0)]
        elif len(self._queue) > 0:
            toreturn = [self._queue.pop(0)]
        else:
            toreturn = []

        if len(self._queue) == 0 and len(self._vip_queue) == 0 and\
                                                self._handler is not None:
            gobject.source_remove(self._handler)
            self._handler = None
        self._lock.release()
        return toreturn
