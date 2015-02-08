# GNU Solfege - free ear training software
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2006, 2007, 2008, 2011  Tom Cato Amundsen
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
import gtk
import gobject
import pango
from solfege.mpd import elems
from solfege.mpd import engravers
from solfege.mpd import parser
from solfege.mpd.rat import Rat

class MusicDisplayer(gtk.ScrolledWindow):
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        self.m_callback = None
        self.m_engravers = []
        self.m_fontsize = 20
        self.m_clickables = []
        self.g_d = gtk.DrawingArea()
        self.g_d.show()

        self.add_with_viewport(self.g_d)
        self.g_d.connect("expose_event", self.on_expose_event)
        self.g_d.add_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.POINTER_MOTION_MASK)
        self.g_d.connect("button_press_event", self.on_button_press_event)

        self.m_width = self.m_height = 0
    def clear(self, numstaff=1):
        if numstaff == 0:
            self.m_engravers = []
        else:
            sc = elems.Score()
            for x in range(numstaff):
                sc.add_staff()
            self.m_engravers = engravers.ScoreContext(sc).m_contexts
        self.g_d.queue_draw()
        dim = engravers.dimentions[20]
        self.set_size_request(self.get_size_request()[0], numstaff*dim.staff_spacing+dim.first_staff_ypos)
    def display(self, music, fontsize, last_timepos=None):
        """Exception handling should be done by the caller."""
        score = parser.parse_to_score_object(music)
        sc = engravers.ScoreContext(score, last_timepos)
        self.m_engravers = sc.m_contexts
        self.m_fontsize = fontsize
        self._display()
    def display_score(self, score):
        self.m_engravers = engravers.ScoreContext(score).m_contexts
        self._display()
    def _display(self):
        dim = engravers.dimentions[self.m_fontsize]
        if self.m_engravers:
            self.m_width = 0
            for eng in self.m_engravers:
                if eng:
                    self.m_width = max(self.m_width, max([e.m_xpos for e in eng if not isinstance(e, (engravers.BeamEngraver, engravers.TupletEngraver, engravers.TieEngraver))]))
                    if not isinstance(eng[-1], engravers.BarlineEngraver):
                        self.m_width += 20
            self.m_height = len(self.m_engravers)*dim.staff_spacing+dim.first_staff_ypos
        else:
            # We get here if we try to display a score with no staffs.
            self.m_width = 100
            self.m_height = dim.staff_spacing + dim.first_staff_ypos
        self.set_size_request(self.get_size_request()[0], self.m_height)
        self.g_d.set_size_request(self.m_width, self.m_height-4)
        self.g_d.queue_draw()
    def add_clickable_region(self, x, y, w, h, midi_int):
        self.m_clickables.append({'x':x, 'y':y, 'w':w, 'h':h,
                                  'midi_int': midi_int})
    def on_button_press_event(self, arg1, event):
        if self.m_callback:
            for r in self.m_clickables:
                if r['x'] < event.x < r['x'] + r['w'] \
                   and r['y'] < event.y < r['y'] + r['h']:
                    self.m_callback(r['midi_int'])
    def on_expose_event(self, darea, event):
        self.white_gc = self.g_d.get_style().white_gc
        self.black_gc = self.g_d.get_style().black_gc
        dim = engravers.dimentions[self.m_fontsize]
        d = self.get_allocation()
        if self.m_width < d[2]:
            self.m_width = d[2]
        if self.m_height < d[3]:
            self.m_height = d[3]
        staff_len = self.m_width
        darea.window.draw_rectangle(self.white_gc, True, 0, 0,
                           self.m_width, self.m_height)
        staff_centrum = dim.first_staff_ypos
        self.m_clickables = []
        for staff in self.m_engravers:
            if staff.m_label:
                ct = darea.create_pango_context()
                l = pango.Layout(ct)
                l.set_text(staff.m_label)
                l.set_font_description(pango.FontDescription("Sans 10"))
                darea.window.draw_layout(self.black_gc, 5, staff_centrum - engravers.dim20.linespacing * 6, l)
            for e in staff:
                if isinstance(e, engravers.StemEngraver):
                    continue
                e.engrave(darea, self.black_gc, staff_centrum)
            # stems has to be drawn after noteheads and accidentals
            for e in staff:
                if isinstance(e, engravers.StemEngraver):
                    e.engrave(darea, self.black_gc, staff_centrum)
            # staff lines:
            if isinstance(staff, engravers.RhythmStaffContext):
                linerange = (0,)
            else:
                linerange = range(-2, 3)
            for y in linerange:
                darea.window.draw_line(self.black_gc,
                             0, staff_centrum+dim.linespacing*y,
                             staff_len, staff_centrum+y*dim.linespacing)
            staff_centrum = staff_centrum + dim.staff_spacing


class ChordEditor(MusicDisplayer):
    def __init__(self):
        MusicDisplayer.__init__(self)
        self._yp = None
        self.g_d.connect("button_release_event", self.on_button_release_event)
        self.g_d.connect("event", self.on_event)
        self.m_cursor = None
    def set_cursor(self, cursor):
        self.m_cursor = cursor
    def on_button_release_event(self, arg1, event):
        dim = engravers.dimentions[self.m_fontsize]
        dist = int((event.y - dim.first_staff_ypos) / dim.linespacing * 2)
        self.emit('clicked', dist)
    def on_event(self, drawingarea, event):
        if event.type == gtk.gdk.MOTION_NOTIFY:
            dim = engravers.dimentions[self.m_fontsize]
            dist = int((event.y - dim.first_staff_ypos) / dim.linespacing * 2)
            self._yp = dist
            self.queue_draw()
    def on_expose_event(self, darea, event):
        MusicDisplayer.on_expose_event(self, darea, event)
        dim = engravers.dimentions[self.m_fontsize]
        if self.m_cursor is not None:
            staff_centrum = dim.first_staff_ypos
            if self.m_cursor == 'erase':
                return
            if self.m_cursor == 'notehead':
                eng = engravers.NoteheadEngraver(Rat(0, 1), "20-tight", 0, self._yp, 2, 0, 0, 0)
            else:
                eng = engravers.AccidentalsEngraver(Rat(0, 1), "20-tight", {self._yp: [int(self.m_cursor)]})
            eng.m_xpos = 50
            eng.engrave(darea, self.black_gc, staff_centrum)

gobject.signal_new('clicked', ChordEditor, gobject.SIGNAL_RUN_FIRST,
    gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))


