# vim: set fileencoding=utf-8 :
# GNU Solfege - free ear training software
# Copyright (C) 2010, 2011 Tom Cato Amundsen
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

import os
import shutil

import gobject
import gtk

from solfege import filesystem
from solfege import gu

class NewProfileDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self, _(u"_Create profile\u2026").replace(u"\u2026", "").replace("_", ""))
        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        vbox = gu.hig_dlg_vbox()
        self.vbox.pack_start(vbox)
        #
        label = gtk.Label(_("Enter the name of the new folder:"))
        label.set_alignment(0.0, 0.5)
        vbox.pack_start(label, False)
        #
        self.g_entry = gtk.Entry()
        self.g_entry.connect('changed', self.on_entry_changed)
        self.g_entry.set_activates_default(True)
        vbox.pack_start(self.g_entry, False)
        #
        label = gtk.Label(_("Your profile data will be stored in:"))
        label.set_alignment(0.0, 0.5)
        vbox.pack_start(label, False)
        #
        self.g_profile_location = gtk.Label()
        vbox.pack_start(self.g_profile_location, False)
        #
        self.g_statusbox = gtk.HBox()
        self.g_statusbox.set_no_show_all(True)
        vbox.pack_start(self.g_statusbox, False)
        im = gtk.Image()
        im.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_MENU)
        self.g_statusbox.pack_start(im, False)
        im.show()

        self.g_status = gtk.Label()
        self.g_status.show()
        self.g_statusbox.pack_start(self.g_status, False)
        self.g_entry.set_text(_("New Profile"))
        self.set_default_response(gtk.RESPONSE_ACCEPT)
    def on_entry_changed(self, *w):
        pdir = os.path.join(filesystem.app_data(), u"profiles",
                            self.g_entry.get_text())
        self.g_profile_location.set_text(pdir)
        if os.path.exists(pdir):
            self.g_status.set_text(_("The profile «%s» already exists.") % self.g_entry.get_text())
            self.g_statusbox.show()
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)
        else:
            self.g_statusbox.hide()
            self.g_status.set_text(u"")
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)


class RenameProfileDialog(gtk.Dialog):
    def __init__(self, oldname):
        gtk.Dialog.__init__(self, _(u"_Rename profile\u2026").replace("_", "").replace(u"\u2026", ""))
        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        vbox = gu.hig_dlg_vbox()
        self.vbox.pack_start(vbox)

        label = gtk.Label(_("Rename the profile «%s» to:") % oldname)
        label.set_alignment(0.0, 0.5)
        vbox.pack_start(label, False)

        self.g_entry = gtk.Entry()
        self.g_entry.set_text(oldname)
        self.g_entry.set_activates_default(True)
        self.g_entry.connect('changed', self.on_entry_changed)
        vbox.pack_start(self.g_entry, False)

        self.g_info = gtk.Label()
        self.g_info.set_no_show_all(True)
        vbox.pack_start(self.g_info, False)
        self.set_default_response(gtk.RESPONSE_ACCEPT)
    def on_entry_changed(self, w):
        s = self.g_entry.get_text()
        pdir = os.path.join(filesystem.app_data(), u"profiles", s)
        ok = False
        if not s:
            self.g_info.show()
            self.g_info.set_text("Empty string not allowed")
        elif os.path.exists(pdir):
            self.g_info.show()
            self.g_info.set_text(_("The profile «%s» already exists.") % self.g_entry.get_text())
        else:
            self.g_info.hide()
            ok = True
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, ok)


class ProfileManagerBase(gtk.Dialog):
    def __init__(self, default_profile):
        gtk.Dialog.__init__(self, _("GNU Solfege - Choose User Profile"))
        # We save the initially selected profile, because we need to keep
        # track of it if the user renames it and then presses cancel.
        self.m_default_profile = default_profile
        vbox = gu.hig_dlg_vbox()
        self.vbox.pack_start(vbox, False)
        l = gtk.Label(_("Solfege will save your statistics and test results in the user profile. By adding additional user profiles to Solfege, multiple users can share a user account on the operating system."))
        l.set_alignment(0.0, 0.5)
        l.set_line_wrap(True)
        vbox.pack_start(l)

        hbox = gtk.HBox()
        hbox.set_spacing(gu.hig.SPACE_MEDIUM)
        vbox.pack_start(hbox)
        button_box = gtk.VBox()

        self.g_create_profile = gtk.Button(_(u"_Create profile\u2026"))
        self.g_create_profile.connect('clicked', self.on_create_profile)
        button_box.pack_start(self.g_create_profile, False)

        self.g_rename_profile = gtk.Button(_(u"_Rename profile\u2026"))
        self.g_rename_profile.connect('clicked', self.on_rename_profile)
        button_box.pack_start(self.g_rename_profile, False)

        self.g_delete_profile = gtk.Button(_(u"_Delete profile\u2026"))
        self.g_delete_profile.connect('clicked', self.on_delete_profile)
        button_box.pack_start(self.g_delete_profile, False)

        hbox.pack_start(button_box, False)
        self.g_liststore = liststore = gtk.ListStore(gobject.TYPE_STRING)
        liststore.append((_("Standard profile"),))
        if os.path.exists(os.path.join(filesystem.app_data(), 'profiles')):
            for subdir in os.listdir(os.path.join(filesystem.app_data(),
                'profiles')):
                liststore.append((subdir,))
        #
        self.g_tw = tw = gtk.TreeView(liststore)
        tw.connect('row-activated', lambda a, b, c: self.response(gtk.RESPONSE_ACCEPT))
        tw.set_headers_visible(False)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(None, renderer, text=0)
        tw.append_column(column)
        hbox.pack_start(tw, False)
        tw.show()
        tw.connect('cursor-changed', self.on_cursor_changed)
        tw.set_cursor((0,))
        for idx, s in enumerate(self.g_liststore):
            if s[0] == default_profile:
                tw.set_cursor((idx, ))
        #
        chk = gu.nCheckButton("app", "noprofilemanager", _("D_on't ask at startup"))
        vbox.pack_start(chk, False)
        self.show_all()
    def on_create_profile(self, w):
        dlg = NewProfileDialog()
        dlg.show_all()
        ret = dlg.run()
        if ret == gtk.RESPONSE_ACCEPT:
            pdir = os.path.join(filesystem.app_data(),
                                u"profiles", dlg.g_entry.get_text())
            if not os.path.exists(pdir):
                try:
                    os.makedirs(pdir)
                    self.g_liststore.append((dlg.g_entry.get_text(),))
                    self.g_tw.set_cursor((len(self.g_liststore)-1,))
                except OSError, e:
                    gu.display_exception_message(e)
        dlg.destroy()
    def on_rename_profile(self, w):
        if self.m_default_profile == self.get_profile():
            rename_default = True
        else:
            rename_default = False
        dlg = RenameProfileDialog(self.get_profile())
        dlg.show_all()
        ret = dlg.run()
        if ret == gtk.RESPONSE_ACCEPT:
            path, column = self.g_tw.get_cursor()
            it = self.g_liststore.get_iter(path)
            try:
                os.rename(os.path.join(
                    filesystem.app_data(), u"profiles", self.get_profile()),
                    os.path.join(filesystem.app_data(),
                        u"profiles", dlg.g_entry.get_text()))
                if rename_default:
                    self.m_default_profile = dlg.g_entry.get_text()
            except OSError, e:
                gu.display_exception_message(e)
                dlg.destroy()
                return
            path, column = self.g_tw.get_cursor()
            self.g_liststore.set(self.g_liststore.get_iter(path),
                0, dlg.g_entry.get_text())
        dlg.destroy()
    def on_delete_profile(self, w):
        if gu.dialog_yesno(_("Permanently delete the user profile «%s»?") % self.get_profile(), self):
            path, column = self.g_tw.get_cursor()
            it = self.g_liststore.get_iter(path)
            try:
                shutil.rmtree(os.path.join(filesystem.app_data(), u"profiles", self.get_profile()))
            except OSError, e:
                gu.display_exception_message(e)
                return
            self.g_liststore.remove(it)
            if not self.g_liststore.iter_is_valid(it):
                it = self.g_liststore[-1].iter
            self.g_tw.set_cursor(self.g_liststore.get_path(it))
    def on_cursor_changed(self, treeview):
        path, column = self.g_tw.get_cursor()
        self.g_delete_profile.set_sensitive(bool(path != (0,)))
        self.g_rename_profile.set_sensitive(bool(path != (0,)))
    def get_profile(self):
        """
        Return None if the standard profile is selected.
        Return the directory name for other profiles.
        """
        cursor = self.g_tw.get_cursor()
        if cursor[0] == (0,) or cursor[0] == None:
            return None
        it = self.g_liststore.get_iter(cursor[0])
        return self.g_liststore.get(it, 0)[0]


class ProfileManager(ProfileManagerBase):
    def __init__(self, default_profile):
        ProfileManagerBase.__init__(self, default_profile)
        self.add_button(gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE)
        b = self.add_button(_("_Start GNU Solfege"), gtk.RESPONSE_ACCEPT)
        b.grab_focus()
        self.set_default_response(gtk.RESPONSE_ACCEPT)


class ChangeProfileDialog(ProfileManagerBase):
    def __init__(self, default_profile):
        ProfileManagerBase.__init__(self, default_profile)
        self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT)

