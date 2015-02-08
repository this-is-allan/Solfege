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

import sys

import gtk

from solfege import gu
from solfege import reportbug

class TracebackWindow(gtk.Dialog):
    def __init__(self, show_gtk_warnings):
        gtk.Dialog.__init__(self)
        self.m_show_gtk_warnings = show_gtk_warnings
        self.set_default_size(630, 400)
        self.vbox.set_border_width(8)
        label = gtk.Label(_("GNU Solfege message window"))
        label.set_name('Heading2')
        self.vbox.pack_start(label, False)
        label = gtk.Label(_("Please report this to the bug database or send an email to bug-solfege@gnu.org if the content of the message make you believe you have found a bug."))
        label.set_line_wrap(True)
        self.vbox.pack_start(label, False)
        scrollwin = gtk.ScrolledWindow()
        scrollwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(scrollwin)
        self.g_text = gtk.TextView()
        scrollwin.add(self.g_text)
        self.g_report = gtk.Button()
        self.g_report.connect('clicked', self.do_report)
        box = gtk.HBox()
        self.g_report.add(box)
        im = gtk.image_new_from_stock('gtk-execute', gtk.ICON_SIZE_BUTTON)
        box.pack_start(im)
        label = gtk.Label()
        label.set_text_with_mnemonic(gu.escape(_('_Make automatic bug report')))
        label.set_use_markup(True)
        box.pack_start(label)
        self.action_area.pack_start(self.g_report)
        self.g_close = gtk.Button(stock='gtk-close')
        self.action_area.pack_start(self.g_close)
        self.g_close.connect('clicked', lambda w: self.hide())
    def do_report(self, *v):
        yesno = gu.dialog_yesno(_("Automatic bug reports are often mostly useless because people omit their email address and add very little info about what happened. Fixing bugs is difficult if we cannot contact you and ask for more information.\n\nI would prefer if you open a web browser and report your bug to the bug tracker at http://bugs.solfege.org.\n\nThis will give your bug report higher priority and it will be fixed faster.\n\nAre you willing to do that?"))
        if yesno:
            return
        self.m_send_exception = 'Nothing'
        b = self.g_text.get_buffer()
        d = reportbug.ReportBugWindow(self,
                        b.get_text(b.get_start_iter(), b.get_end_iter()))
        while 1:
            ret = d.run()
            if ret in (gtk.RESPONSE_REJECT, gtk.RESPONSE_DELETE_EVENT):
                break
            elif ret == reportbug.RESPONSE_SEND:
                self.m_send_exception = d.send_bugreport()
                break
        if self.m_send_exception != 'Nothing':
            if self.m_send_exception:
                m = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                    "Sending bugreport failed:\n%s" % self.m_send_exception)
            else:
                m = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
                    gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE,
                    'Report sent to http://www.solfege.org')
            m.run()
            m.destroy()
        d.destroy()
    def write(self, txt):
        if ("DeprecationWarning:" in txt) or \
           (not self.m_show_gtk_warnings and (
            "GtkWarning" in txt
            or "PangoWarning" in txt
            or ("Python C API version mismatch" in txt and
                ("solfege_c_midi" in txt or "swig" in txt))
            )):
            return
        sys.stdout.write(txt)
        if txt.strip():
            self.show_all()
        buffer = self.g_text.get_buffer()
        buffer.insert(buffer.get_end_iter(), txt)
        self.set_focus(self.g_close)
    def flush(self, *v):
        pass
    def close(self, *v):
        pass
