# GNU Solfege - free ear training software
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2007, 2008, 2011  Tom Cato Amundsen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import gobject
import gtk

from solfege import cfg
from solfege import mpd

DELAY1 = 500
DELAY2 = 50

class NotenameSpinButton(gtk.HBox):
    def __init__(self, default_value):
        gtk.HBox.__init__(self)
        self.m_value = mpd.notename_to_int(default_value)
        self.g_label = gtk.Label(mpd.int_to_user_octave_notename(self.m_value))
        self.g_label.set_use_markup(1)
        frame = gtk.Frame()
        e = gtk.EventBox()
        frame.add(e)
        self.pack_start(frame, False)
        self.g_label.set_size_request(60, -1)#FIXME hardcoded value
        frame.set_shadow_type(gtk.SHADOW_IN)
        e.add(self.g_label)
        vbox = gtk.VBox()
        self.pack_start(vbox, False)
        # up
        self.g_up = gtk.Arrow(gtk.ARROW_UP, gtk.SHADOW_OUT)
        eb1 = gtk.EventBox()
        eb1.connect('button-press-event', self.on_up_press)
        eb1.connect('button-release-event', self.on_up_release)
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_OUT)
        frame.add(self.g_up)
        eb1.add(frame)
        vbox.pack_start(eb1)
        # down
        self.g_down = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_ETCHED_IN)
        eb2 = gtk.EventBox()
        eb2.connect('button-press-event', self.on_down_press)
        eb2.connect('button-release-event', self.on_down_release)
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_OUT)
        frame.add(self.g_down)
        eb2.add(frame)
        vbox.pack_start(eb2)
        self.m_timeout = None
    def on_up_press(self, eb, ev):
        if self.m_timeout:
            gobject.source_remove(self.m_timeout)
            self.m_timeout = None
        if ev.type == gtk.gdk.BUTTON_PRESS:
            if self.m_value < 127:
                self.up()
            if self.m_value < 127:
                self.m_timeout = gobject.timeout_add(DELAY1, self.on_up_timeout)
    def on_up_release(self, eb, ev):
        if self.m_timeout:
            gobject.source_remove(self.m_timeout)
            self.m_timeout = None
    def on_up_timeout(self, *v):
        if self.m_value < 127:
            self.up()
            self.m_timeout = gobject.timeout_add(DELAY2, self.on_up_timeout)
    def up(self):
        self.m_value += 1
        self.g_label.set_text(mpd.int_to_user_octave_notename(self.m_value))
        self.g_label.set_use_markup(1)
        self.emit('value-changed', self.m_value)
    def on_down_press(self, eb, ev):
        if self.m_timeout:
            gobject.source_remove(self.m_timeout)
            self.m_timeout = None
        if ev.type == gtk.gdk.BUTTON_PRESS:
            if self.m_value > 0:
                self.down()
            if self.m_value > 0:
                self.m_timeout = gobject.timeout_add(DELAY1, self.on_down_timeout)
    def on_down_release(self, eb, ev):
        if self.m_timeout:
            gobject.source_remove(self.m_timeout)
            self.m_timeout = None
    def on_down_timeout(self, *v):
        if self.m_value > 0:
            self.down()
            self.m_timeout = gobject.timeout_add(DELAY2, self.on_down_timeout)
    def down(self):
        self.m_value -= 1
        self.g_label.set_text(mpd.int_to_user_octave_notename(self.m_value))
        self.g_label.set_use_markup(1)
        self.emit('value-changed', self.m_value)
    def get_value(self):
        return self.m_value
    def set_value(self, val):
        self.m_value = val
        self.g_label.set_text(mpd.int_to_user_octave_notename(val))
        self.g_label.set_use_markup(1)

gobject.signal_new('value-changed', NotenameSpinButton,
                   gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))


class NotenameRangeController(object):
    def __init__(self, spin_low, spin_high, lowest_value, highest_value):
        self.g_spin_low = spin_low
        self.g_spin_low.connect('value-changed', self.on_low_changed)
        self.g_spin_high = spin_high
        self.g_spin_high.connect('value-changed', self.on_high_changed)
        self.m_lowest_value = mpd.notename_to_int(lowest_value)
        self.m_highest_value = mpd.notename_to_int(highest_value)
    def on_low_changed(self, widget, v):
        if widget.get_value() > self.g_spin_high.get_value():
            self.g_spin_low.set_value(self.g_spin_high.get_value())
        elif widget.get_value() < self.m_lowest_value:
            self.g_spin_low.set_value(self.m_lowest_value)
    def on_high_changed(self, widget, v):
        if widget.get_value() < self.g_spin_low.get_value():
            self.g_spin_high.set_value(self.g_spin_low.get_value())
        elif widget.get_value() > self.m_highest_value:
            self.g_spin_high.set_value(self.m_highest_value)

class nNotenameRangeController(NotenameRangeController, cfg.ConfigUtils):
    def __init__(self, spin_low, spin_high, lowest_value, highest_value,
                 exname, name_low, name_high):
        NotenameRangeController.__init__(self, spin_low, spin_high,
                lowest_value, highest_value)
        cfg.ConfigUtils.__init__(self, exname)
        self.m_name_low = name_low
        self.m_name_high = name_high
        low = mpd.notename_to_int(self.get_string(self.m_name_low))
        high = mpd.notename_to_int(self.get_string(self.m_name_high))
        if low > high:
            low = high
        self.g_spin_low.set_value(low)
        self.g_spin_high.set_value(high)
    def on_low_changed(self, w, v):
        NotenameRangeController.on_low_changed(self, w, v)
        self.set_string(self.m_name_low, mpd.int_to_octave_notename(self.g_spin_low.get_value()))
    def on_high_changed(self, w, v):
        NotenameRangeController.on_high_changed(self, w, v)
        self.set_string(self.m_name_high, mpd.int_to_octave_notename(self.g_spin_high.get_value()))
    def set_range(self, lowest_value, highest_value):
        """
        Set the lowest and highest tone allowed.
        make a separate function for NotenameRangeController if we need it.
        """
        assert mpd.compare_notenames(lowest_value, highest_value) <= 0
        self.m_lowest_value = mpd.notename_to_int(lowest_value)
        self.m_highest_value = mpd.notename_to_int(highest_value)
        if self.m_lowest_value > self.g_spin_low.get_value():
            self.set_string(self.m_name_low, lowest_value)
            self.g_spin_low.set_value(self.m_lowest_value)
        if self.m_highest_value < self.g_spin_high.get_value():
            self.set_string(self.m_name_high, highest_value)
            self.g_spin_high.set_value(self.m_highest_value)

