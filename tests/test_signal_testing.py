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

import unittest
import gobject
import uuid

from tests.signals_testing import SignalCatcher, GobjectSignalsManager

class TestSignalTesting(unittest.TestCase):

    def setUp(self):
        self.gobject_signal_manager = GobjectSignalsManager()
        self.gobject_signal_manager.init_signals()

    def tearDown(self):
        self.gobject_signal_manager.terminate_signals()

    def test_signal_catching(self):
        generator = FakeGobject()
        arg = str(uuid.uuid4())
        with SignalCatcher(self, generator, 'one') \
                as [signal_catched_event, signal_arguments]:
            generator.emit_signal('one', arg)
            signal_catched_event.wait()
        self.assertEqual(len(signal_arguments), 1)
        self.assertEqual(len(signal_arguments[0]), 1)
        one_signal_arguments = signal_arguments[0]
        self.assertEqual(arg, one_signal_arguments[0])

#    @unittest.skip("It is slow and do not affect the current code")
#    def test_signal_missing(self):
#        generator = FakeGobject()
#        arg = str(uuid.uuid4())
#        with SignalCatcher(self, generator, 'two', False, error_code = None) \
#                as [signal_catched_event, signal_arguments]:
#            generator.emit_signal('one', arg)
#            signal_catched_event.wait()
#        self.assertEqual(len(signal_arguments), 0)


class FakeGobject(gobject.GObject):
    __gsignals__ = {'one': (gobject.SIGNAL_RUN_FIRST,
                               gobject.TYPE_NONE, (str, )),
                    'two': (gobject.SIGNAL_RUN_FIRST,
                               gobject.TYPE_NONE, (str, ))}

    def emit_signal(self, signal_name, argument):
        gobject.idle_add(self.emit, signal_name, argument)


def test_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestSignalTesting)
