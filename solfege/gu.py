# GNU Solfege - free ear training software
# vim: set fileencoding=utf-8 :
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
from __future__ import division

import os
import re
import subprocess
import sys
import time
import traceback

import gobject
import gtk
import pango

from solfege import cfg
from solfege import osutils
from solfege import soundcard
from solfege import utils

import solfege

PAD = 8
PAD_SMALL = 4

#  Prefixes used in this module:
#  t  pack into a table, the first five parameters are table, x1, x2, y1, y2
#  n  a widget that get its state stored in ~/.solfegerc
#  b  the widget is packed into the first argument

def escape(s):
    """
    All strings that are passed to gtk.Label.set_markup, or as ordinary
    text, if we later call set_use_markup, should be escaped.
    """
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    return s.replace(">", "&gt;")

def get_modifier(s):
    m = (('<ctrl>', gtk.gdk.CONTROL_MASK),
         ('<shift>', gtk.gdk.SHIFT_MASK),
         ('<alt>', gtk.gdk.MOD1_MASK))
    for mod, mask in m:
        if s.startswith(mod):
            return mask, s[len(mod):]
    return None, s

def parse_key_string(string):
    if not string:
        return None, None
    mod = 0
    m, s = get_modifier(string)
    while m:
        mod = mod + m
        m, s = get_modifier(s)
    if len(s) == 1:
        return mod, ord(s)
    else:
        return mod, getattr(gtk.keysyms, s)



def tLabel(table, x1, x2, y1, y2, text="", xalign=0.0, yalign=0.5, xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL, xpadding=0, ypadding=0):
    label = gtk.Label(text)
    label.set_alignment(xalign, yalign)
    table.attach(label, x1, x2, y1, y2, xoptions=xoptions, yoptions=yoptions, xpadding=xpadding, ypadding=ypadding)
    return label

def bLabel(pack_into, label, expand=True, fill=True):
    b = gtk.Label(label)
    b.show()
    pack_into.pack_start(b, expand, fill)
    return b

def bButton(pack_into, label, callback=None, expand=True, fill=True):
    b = gtk.Button(label)
    b.show()
    if callback:
        b.connect('clicked', callback)
    pack_into.pack_start(b, expand, fill)
    return b

class nSpinButton(gtk.SpinButton, cfg.ConfigUtils):#FIXME (??what is there to fix???)
    def __init__(self, exname, name, adj, climb_rate=1, digits=1):
        gtk.SpinButton.__init__(self, adj, climb_rate, digits)
        cfg.ConfigUtils.__init__(self, exname)
        self.m_name = name
        self.set_digits(0)
        self.show()
        self.set_alignment(1)
        self.set_value(self.get_float(self.m_name))
        if self.get_value() != self.get_float(self.m_name):
            self.set_float(self.m_name, self.get_value())
        self.connect('value-changed', self.on_changed)
        self._watch_id = self.add_watch(self.m_name, self._watch_cb)
        self.m_stop_watch = 0
    def _watch_cb(self, name):
        if not self.m_stop_watch:
            gtk.SpinButton.set_value(self, self.get_float(name))
    def set_value(self, value):
        gtk.SpinButton.set_value(self, value)
        self.set_float(self.m_name, value)
    def on_changed(self, _o):
        self.m_stop_watch = 1
        self.set_float(self.m_name, self.get_value())
        self.m_stop_watch = 0

def tSpinButton(table, x1, x2, y1, y2,
                value, lower, upper, step_incr=1, page_incr=10, callback=None):
    adj = gtk.Adjustment(value, lower, upper, step_incr, page_incr)
    spin = gtk.SpinButton(adj, digits=0)
    if callback:
        spin.connect('value-changed', callback)
    table.attach(spin, x1, x2, y1, y2)
    return spin

def bHBox(pack_into, expand=True, fill=True, padding=0):
    b = gtk.HBox()
    b.show()
    pack_into.pack_start(b, expand, fill, padding)
    return b

def bVBox(pack_into, expand=True, fill=True, padding=0):
    b = gtk.VBox()
    pack_into.pack_start(b, expand, fill, padding)
    return b

class nCheckButton(gtk.CheckButton, cfg.ConfigUtils):
    def __init__(self, exname, name, label=None, default_value=0, callback=None):
        gtk.CheckButton.__init__(self, label)
        #cfg.ConfigUtils.__init__(self, exname)
        cfg.ConfigUtils.__dict__['__init__'](self, exname)
        self.m_name = name
        self.m_callback = callback
        self.show()
        if default_value:
            s = "true"
        else:
            s = "false"
        self.set_bool(self.m_name, self.get_bool(self.m_name+"="+s))
        if self.get_bool(self.m_name):
            self.set_active(1)
        self._clicked_id = self.connect('toggled', self.on_clicked)
        self._watch_id = self.add_watch(self.m_name, self._watch_cb)
    def _watch_cb(self, name):
        self.set_active(self.get_bool(name))
    def on_clicked(self, _o):
        self.set_bool(self.m_name, self.get_active())
        if self.m_callback:
            self.m_callback(_o)

def RadioButton(group, label, callback=None):
    rdb = gtk.RadioButton(group, label)
    if callback:
        rdb.connect('toggled', callback)
    rdb.show()
    return rdb

def nComboBox(exname, name, default, popdown_strings):
    c = gtk.combo_box_new_text()
    for n in popdown_strings:
        c.append_text(n)
    c.m_exname = exname
    c.m_name = name
    val = cfg.get_string("%s/%s=X" % (c.m_exname, c.m_name))
    if val == 'X':
        cfg.set_int("%s/%s" % (exname, name),
            popdown_strings.index(default))
        c.set_active(popdown_strings.index(default))
    else:
        try:
            i = cfg.get_int("%s/%s" % (c.m_exname, c.m_name))
        except ValueError:
            i = 0
            cfg.set_int("%s/%s" % (c.m_exname, c.m_name), 0)
        if i >= len(popdown_strings):
            i = 0
            cfg.set_int("%s/%s" % (c.m_exname, c.m_name), 0)
        c.set_active(cfg.get_int("%s/%s" % (c.m_exname, c.m_name)))
    def f(combobox):
        cfg.set_int("%s/%s" % (exname, name), combobox.get_active())
    c.connect('changed', f)
    return c


class nCombo(gtk.Combo, cfg.ConfigUtils):
    def __init__(self, exname, name, default, popdown_strings):
        """
        Be aware that the value of the entry, is stored as an integer
        popdown_strings.index(entry.get_text()), so if popdown_strings
        changes when upgrading the program, the value of the combo
        might change.

        Despite this problems, I do it this way, because if we store
        the actual value of the entry, we get into trouble when running
        the program with other locale settings.
        """
        gtk.Combo.__init__(self)
        #cfg.ConfigUtils.__init__(self, exname)
        cfg.ConfigUtils.__dict__['__init__'](self, exname)
        self.popdown_strings = popdown_strings
        self.m_name = name
        self.set_value_in_list(True, False)
        self.set_popdown_strings(popdown_strings)
        i = self.get_int_with_default(name, -1)
        if i == -1:
            i = popdown_strings.index(default)
        self.entry.set_text(popdown_strings[i])
        self.entry.connect("changed", self.entry_changed)
        self.entry.set_editable(False)
        self.show()
    def entry_changed(self, entry):
        self.set_int(self.m_name, self.popdown_strings.index(entry.get_text()))

class PercussionInstrumentMenu(gtk.Menu):
    def __init__(self, callback):
        gtk.Menu.__init__(self)
        for idx, pname in enumerate(soundcard.percussion_names):
            menuitem = gtk.MenuItem(pname)
            menuitem.connect('activate', callback, idx)
            self.append(menuitem)
            menuitem.show()
        self.show()


class PercussionNameButton(gtk.Button, cfg.ConfigUtils):
    def __init__(self, exname, name, default):
        gtk.Button.__init__(self)
        cfg.ConfigUtils.__init__(self, exname)
        self.m_name = name
        self.g_menu = PercussionInstrumentMenu(self.entry_changed)
        i = self.get_int(name)
        if not i:
            i = soundcard.percussionname_to_int(default)
            self.set_int(name, i)
        self.set_label(soundcard.int_to_percussionname(i))
        self.connect('clicked', lambda w: self.g_menu.popup(None, None, None, 1, 0))
    def entry_changed(self, widget, value):
        self.set_int(self.m_name, value + soundcard.first_percussion_int_value)
        self.set_label(soundcard.percussion_names[value])
        t = utils.new_percussion_track()
        t.note(8, value + soundcard.first_percussion_int_value)
        t.note(16, value + soundcard.first_percussion_int_value)
        t.note(16, value + soundcard.first_percussion_int_value)
        t.note(4, value + soundcard.first_percussion_int_value)
        soundcard.synth.play_track(t)

class FlashBar(gtk.Frame):
    def __init__(self):
        gtk.Frame.__init__(self)
        self.set_shadow_type(gtk.SHADOW_IN)
        self.__stack = []
        self.__label = HarmonicProgressionLabel('')
        self.__content = gtk.HBox()
        self.__content.show()
        self.add(self.__content)
        self.__timeout = None
        # The allocated size
        self.m_sx, self.m_sy = 0, 0
    def require_size(self, stringlist):
        """
        stringlist is a list of the strings believed to be widest.
        require_size will make sure that the flashbar is at least large enough to
        show all the strings in stringlist.
        """
        for s in stringlist:
            self.display(s)
        self.empty()
    def delayed_flash(self, milliseconds, msg):
        gobject.timeout_add(milliseconds, lambda: self.flash(msg))
    def empty(self):
        for child in self.__content.get_children():
            child.destroy()
    def flash(self, txt, **kwargs):
        """Display a message that is automatically removed after some time.
        If we flash a new message before the old flashed message are removed,
        we old flashed message are removed.
        """
        if self.__timeout:
            gobject.source_remove(self.__timeout)
        self.display(txt, **kwargs)
        def f(self=self):
            self.__timeout = None
            if self.__stack:
                self.display(self.__stack[-1][0], **self.__stack[-1][1])
            else:
                self.empty()
        self.__timeout = gobject.timeout_add(2000, f)
    def push(self, txt, **kwargs):
        # stop any flashing before we push
        self.display(txt, **kwargs)
        self.__stack.append((txt, kwargs))
    def display(self, txt, **kwargs):
        self.empty()
        r = re.compile("(\{\w+\})") # Unicode??
        self.set_size_request(-1, -1)
        for child in r.split(txt):
            m = r.match(child)
            if m:
                varname = child[1:][:-1]
                from solfege import lessonfilegui
                if isinstance(kwargs[varname], basestring):
                    w = gtk.Label(kwargs[varname])
                    w.set_name("FlashBarLabel")
                else:
                    w = lessonfilegui.new_labelobject(kwargs[varname])
            elif child: # don't create label for empty string
                w = gtk.Label(child)
                w.set_name("FlashBarLabel")
            self.__content.pack_start(w, False)
            w.show()
        sx, sy = self.size_request()
        self.m_sx = max(sx, self.m_sx)
        self.m_sy = max(sy, self.m_sy)
        self.set_size_request(self.m_sx, self.m_sy)
        if self.__timeout:
            gobject.source_remove(self.__timeout)
            self.__timeout = None
    def pop(self):
        """If a message is being flashed right now, that flashing is
        not affected, but the message below the flashed message is removed.
        """
        if self.__stack:
            self.__stack.pop()
        if not self.__timeout:
            if self.__stack:
                self.display(self.__stack[-1][0],
                           **self.__stack[-1][1])
            else:
                self.empty()
    def clear(self):
        self.__stack = []
        if not self.__timeout:
            self.empty()
    def set(self, txt, **kwargs):
        """
        Empty the stack of messages and display the string in txt.
        """
        self.__stack = [(txt, kwargs)]
        self.display(txt, **kwargs)

class hig(object):
    SPACE_SMALL= 6
    SPACE_MEDIUM = 12
    SPACE_LARGE = 18

class hig_dlg_vbox(gtk.VBox):
    """a GtkVBox containing as many rows as you wish to have categories
    inside the control area of the GtkDialog.
    """
    spacing = 12
    border_width = 18
    def __init__(self):
        gtk.VBox.__init__(self)
        self.set_spacing(self.spacing)
        self.set_border_width(self.border_width)

def hig_category_vbox(title, spacing=6):
    """
    spacing  the space to put between children. HIG say is should be 6, but
    while packing gtk.LinkButtons there is too much space between the links
    when packing with 6 pixels. So I added the spacing parameter.
    Return a tuple of two boxes:
    box1 -- a box containing everything including the title. Useful
            if you have to hide a category.
    box2    The box you should pack your stuff in.
    """
    vbox = gtk.VBox()
    vbox.set_spacing(6)
    label = gtk.Label('<span weight="bold">%s</span>' % title)
    label.set_use_markup(True)
    label.set_alignment(0.0, 0.0)
    vbox.pack_start(label, False)
    hbox = gtk.HBox()
    vbox.pack_start(hbox, False)
    fill = gtk.Label("    ")
    hbox.pack_start(fill, False)
    category_content_vbox = gtk.VBox()
    hbox.pack_start(category_content_vbox, True)
    category_content_vbox.set_spacing(spacing)
    vbox.show_all()
    return vbox, category_content_vbox

def hig_label_widget(txt, widget, sizegroup, expand=False, fill=False):
    """
    Return a box containing a label and a widget, aligned nice
    as the HIG say we should. widget could also be a list or tuple of
    widgets.
    """
    hbox = gtk.HBox()
    hbox.set_spacing(6)
    label = gtk.Label(txt)
    label.set_alignment(0.0, 0.5)
    if sizegroup:
        sizegroup.add_widget(label)
    hbox.pack_start(label, False)
    if not isinstance(widget, (list, tuple)):
        widget = [widget]
    for w in widget:
        hbox.pack_start(w, fill, expand)
    label.set_use_underline(True)
    label.set_mnemonic_widget(widget[0])
    return hbox

class SpinButtonRangeController(object):
    def __init__(self, spin_low, spin_high, lowest_value, highest_value):
        self.g_spin_low = spin_low
        self.g_spin_low.connect('value-changed', self.on_low_changed)
        self.g_spin_high = spin_high
        self.g_spin_high.connect('value-changed', self.on_high_changed)
        self.m_lowest_value = lowest_value
        self.m_highest_value = highest_value
    def on_low_changed(self, widget, *v):
        if widget.get_value() > self.g_spin_high.get_value():
            self.g_spin_low.set_value(self.g_spin_high.get_value())
        elif widget.get_value() < self.m_lowest_value:
            self.g_spin_low.set_value(self.m_lowest_value)
    def on_high_changed(self, widget, *v):
        if widget.get_value() < self.g_spin_low.get_value():
            self.g_spin_high.set_value(self.g_spin_low.get_value())
        elif widget.get_value() > self.m_highest_value:
            self.g_spin_high.set_value(self.m_highest_value)

def create_stock_menu_item(stock, txt, callback, ag, accel_key, accel_mod):
    box = gtk.HBox()
    box.set_spacing(PAD_SMALL)
    im = gtk.Image()
    im.set_from_stock(stock, gtk.ICON_SIZE_MENU)
    item = gtk.ImageMenuItem(txt)
    item.set_image(im)
    if accel_key != 0:
        item.add_accelerator('activate', ag, accel_key, accel_mod, gtk.ACCEL_VISIBLE)
    item.connect('activate', callback)
    return item

class AlignedHBox(gtk.HBox):
    def setup_pre(self):
        self.g_prebox = gtk.HBox()
        self.g_prebox.set_no_show_all(True)
        self.pack_start(self.g_prebox)
    def setup_post(self):
        self.g_postbox = gtk.HBox()
        self.g_postbox.set_no_show_all(True)
        self.pack_start(self.g_postbox)
    def set_alignment(self, xalign, yalign):
        self.m_xalign = xalign
        self.m_yalign = yalign
        if xalign == 0.0:
            self.g_prebox.hide()
            self.g_postbox.show()
        elif xalign == 0.5:
            self.g_prebox.show()
            self.g_postbox.show()
        elif xalign == 1.0:
            self.g_prebox.show()
            self.g_postbox.hide()

class HarmonicProgressionLabel(AlignedHBox):
    """
    This class can parse strings like I-(6,4)V(5,3)-I and can be used
    as button labels.
    """
    def __init__(self, text):
        AlignedHBox.__init__(self)
        self.show()
        self.m_xalign = 0.5
        self.m_yalign = 0.5
        self.set_text(text)
    def set_text(self, text):
        for o in self.get_children():
            o.destroy()
        self.m_str = text 
        self.setup_pre()
        while self.m_str:
            T, A, B = self.get_next_token()
            if T == 'big' or T == 'err':
                self.bigchar(A)
            elif T == 'two':
                self.twoline(A, B)
            else:
                assert T == 'one'
                self.oneline(A)
        self.setup_post()
        self.show_all()
        self.set_alignment(self.m_xalign, self.m_yalign)
    def get_next_token(self):
        m_re1 = re.compile("([^\(]+)", re.UNICODE)
        m_re2 = re.compile("\((\w*),\s*(\w*)\)", re.UNICODE)
        m_re3 = re.compile("\((\w*)\)", re.UNICODE)
        m1 = m_re1.match(self.m_str)
        m2 = m_re2.match(self.m_str)
        m3 = m_re3.match(self.m_str)
        if m1:
            self.m_str = self.m_str[len(m1.group()):]
            return "big", m1.groups()[0], None
        if m2:
            self.m_str = self.m_str[len(m2.group()):]
            return "two", m2.groups()[0], m2.groups()[1]
        if m3:
            self.m_str = self.m_str[len(m3.group()):]
            return "one", m3.groups()[0], None
        c = self.m_str[0]
        return "err", c, None
    def twoline(self, A, B):
        vbox = gtk.VBox()
        t1 = gtk.Label(A)
        t1.set_name("ProgressionLabelNumber")
        t1.show();vbox.pack_start(t1);
        t1.set_alignment(0, 0);
        t2 = gtk.Label(B)
        t2.set_name("ProgressionLabelNumber")
        t2.show();vbox.pack_start(t2);
        t2.set_alignment(0, 0);
        self.pack_start(vbox, False)
    def oneline(self, A):
        vbox = gtk.VBox()
        t = gtk.Label(A)
        t.set_name("ProgressionLabelNumber")
        t.show();vbox.pack_start(t);
        t.set_alignment(0, 0);
        self.pack_start(vbox, False)
    def bigchar(self, A):
        t1 = gtk.Label(A)
        t1.set_name("ProgressionNameLabel")
        t1.show()
        self.pack_start(t1, False)


def dialog_yesno(text, parent=None, default=False):
    """Return True if the answer is yes, False if the answer is no.
    """
    m = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_YES_NO, text)
    if default:
        m.set_default_response(gtk.RESPONSE_YES)
    ret = m.run()
    m.destroy()
    return ret == gtk.RESPONSE_YES

def dialog_ok(text, parent=None, secondary_text=None, msgtype=gtk.MESSAGE_INFO):
    """"
    Return the gtk.RESPONSE_XXXX returned by .run()
    """
    m = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, msgtype,
            gtk.BUTTONS_OK, text)
    if secondary_text:
        m.format_secondary_text(secondary_text)
    ret = m.run()
    m.destroy()
    return ret

def dialog_delete(text, parent, secondary_text=None):
    m = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_NONE, text)
    m.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_DELETE, gtk.RESPONSE_ACCEPT)
    if secondary_text:
        m.format_secondary_text(secondary_text)
    ret = m.run()
    m.destroy()
    return ret == gtk.RESPONSE_ACCEPT
    return ret

class NewLineBox(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        self.m_todo_widgets = []
    def add_widget(self, widget):
        self.m_todo_widgets.append(widget)
    def show_widgets(self):
        if 'newline' in self.m_todo_widgets:
            self._newline_show_widgets()
        else:
            self._flow_show_widgets()
    def newline(self):
        self.m_todo_widgets.append('newline')
    def _newline_show_widgets(self):
        sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        hbox = bHBox(self, True)
        for n in self.m_todo_widgets:
            if n == 'newline':
                hbox = bHBox(self, False)
            else:
                hbox.pack_start(n, False)
                sizegroup.add_widget(n)
    def _flow_show_widgets(self):
        w = 8
        num_lines = len(self.m_todo_widgets) // w + 1
        w = len(self.m_todo_widgets) // num_lines + 1
        sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        c = 0
        for n in self.m_todo_widgets:
            sizegroup.add_widget(n)
            if c % w == 0:
                hbox = bHBox(self, True, True)
            hbox.pack_start(n, False)
            c += 1
        self.show_all()
    def empty(self):
        self.foreach(lambda w: w.destroy())
        self.m_todo_widgets = []
    def get_max_child_height(self):
        return max([c.size_request()[1] for c in self.m_todo_widgets])

def create_png_image(fn):
    """
    Create an image by loading a png file from graphics dir
    """
    im = gtk.Image()
    im.set_from_file(os.path.join('graphics', fn)+'.png')
    im.show()
    return im

def create_rhythm_image(rhythm):
    """
    rhythm : a string like 'c8 c8' or 'c8 c16 c16'
    The image returned is shown.
    """
    im = gtk.Image()
    im.set_from_file(os.path.join('graphics', 'rhythm-%s.png' % (rhythm.replace(" ", ""))))
    im.show()
    return im

def decode_filename(filename):
    """
    Decode the filename we get from FileChooser.get_filename()
    We need to do this for every filename.
    """
    if sys.platform == 'win32':
        return filename.decode("utf-8")
    else:
        return filename.decode(sys.getfilesystemencoding())


class EditorDialogBase(object):
    # Classes inheriting from this must define self.savedir
    instance_counter = 1
    # We use a special key (None, self.m_instance_number) for files
    # that are new and don't have a real filename yet. Other files use
    # their file name as key.
    instance_dict = {}
    def __init__(self, filename=None):
        self.m_instance_number = EditorDialogBase.instance_counter
        EditorDialogBase.instance_counter += 1
        self.m_filename = filename
        self.m_savetime = time.time()
        self.connect('delete_event', self.on_delete_event)
        self.g_ui_manager = gtk.UIManager()
        accelgroup = self.g_ui_manager.get_accel_group()
        self.add_accel_group(accelgroup)

        self.g_actiongroup = gtk.ActionGroup('')
        self.g_actiongroup.add_actions([
         ('Close', gtk.STOCK_CLOSE, None, None, None, self.close_window),
         ('Save', gtk.STOCK_SAVE, None, None, None, self.on_save),
         ('SaveAs', gtk.STOCK_SAVE_AS, None, None, None, self.on_save_as),
         ('New', gtk.STOCK_NEW, None, None, None, self.new_file),
         ('Open', gtk.STOCK_OPEN, None, None, None, self.on_open),
         ('Help', gtk.STOCK_HELP, None, None, None, self.on_show_help),
        ])
    def add_to_instance_dict(self):
        if self.m_filename:
            assert self.m_filename not in self.instance_dict
            self.instance_dict[self.m_filename] = self
        else:
            assert (None, self.m_instance_number) not in self.instance_dict
            self.instance_dict[(None, self.m_instance_number)] = self
    def get_idict_key(self):
        """
        Return the key used to store the editor in .instance_dict.
        This will return (None, self.m_instance_number) if we don't have
        a file name, else return the filename.
        """
        return self.m_filename if self.m_filename else (None, self.m_instance_number)
    def _get_a_filename(self):
        """
        Return a file name. UntitledN (where N is an integer) if we
        have to real name.
        """
        if not self.m_filename:
            return _("Untitled%s") % self.m_instance_number
        return self.m_filename
    def do_closing_stuff(self):
        """
        Classes that need to do stuff before we return from the delete-event
        callback should implement this method.
        """
        del self.instance_dict[self.get_idict_key()]
    def close_window(self, *w):
        """
        Close the window if allowed.
        Return True if closed
        Return False if cancelled by the user.
        """
        r = self.on_delete_event()
        if not r:
            self.destroy()
        return not r
    def can_we_close_window(self, *w):
        """
        Return True if we can close the window.
        If we have unsaved changes, the user will be asked to
        Save, Cancel or Discard.
        Return False if canceled because of unsaved changes.
        """
        if not self.m_changed or self.do_save_dialog():
            return True
        else:
            return False
    def do_save_dialog(self):
        """
        Display a dialog asking if we want to save, and do save if necessary.
        Return True if we can destroy the dialog.
        """
        m = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
            gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE,
            _("Save changes to \"%s\" before closing?") % self._get_a_filename())
        t = time.time() - self.m_savetime
        if t < 60:
            msg = _("If you don't save, changes from the past %i seconds will be permanently lost.") % int(time.time() - self.m_savetime)
        else:
            msg = _("If you don't save, changes from the past %i minutes will be permanently lost.") % int((time.time() - self.m_savetime) / 60.0)
        m.format_secondary_text(msg)
        m.add_button(_("_Close without Saving"), gtk.RESPONSE_CLOSE)
        m.add_button("gtk-cancel", gtk.RESPONSE_CANCEL)
        m.add_button("gtk-save", gtk.RESPONSE_OK)
        m.set_default_response(gtk.RESPONSE_OK)
        r = m.run()
        m.destroy()
        if r == gtk.RESPONSE_CLOSE:
            return True
        elif r in (gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT):
            return False
        else:
            assert r == gtk.RESPONSE_OK
            self.on_save()
            return True
    def on_delete_event(self, *ignore):
        """
        Do as GTK delete-event handlers should do:
          Return True if the window should not be deleted.
          Return False if it should be deleted.
        """
        do_close = self.can_we_close_window()
        if do_close:
            self.do_closing_stuff()
            return False
        return True
    def on_open(self, widget):
        """
        Open a FileChooserDialog and select a file.
        Load into this editor window if it is empty and unused,
        if not load into a new one.

        This method will catch exceptions raised while loading the file
        and display a dialog. Then it will destroy any newly created
        dialog.
        """
        dialog = gtk.FileChooserDialog(None, self,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
             gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_current_folder(self.savedir)
        ret = dialog.run()
        if ret == gtk.RESPONSE_OK:
            try:
                new_file = decode_filename(dialog.get_filename())
                assert new_file not in self.instance_dict
                win = self.__class__(new_file)
                win.show_all()
                win.set_title(new_file)
                if (not self.m_filename) and (not self.m_changed):
                    del self.instance_dict[self.get_idict_key()]
                    self.destroy()
            except Exception, e:
                # Since we catch all sorts of exceptions here, we don't have
                # to do handle string to int conversion in
                # PractiseSheet.parse_file. Just let int() raise ValueException
                # if the string in not an integer.
                if 'msg1' in dir(e):
                    solfege.win.display_error_message2(getattr(e, 'msg1', ''),
                        getattr(e, 'msg2', ''))
                else:
                    display_exception_message(e)
        dialog.destroy()
    def get_save_as_dialog(self):
        dialog = gtk.FileChooserDialog(_("Save As..."), self,
            gtk.FILE_CHOOSER_ACTION_SAVE,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
             gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        return dialog
    def on_save_as(self, widget):
        """
        Return True if the file was saved, False if not.
        """
        dialog = self.get_save_as_dialog()
        if not os.path.exists(self.savedir):
            try:
                os.mkdir(self.savedir)
            except OSError, e:
                pass
        if self.m_filename and os.path.commonprefix([
               self.savedir, os.path.dirname(self.m_filename)]) == self.savedir:
            dialog.set_current_folder(os.path.dirname(self.m_filename))
        else:
            dialog.set_current_folder(self.savedir)
        while 1:
            ret = dialog.run()
            if ret == gtk.RESPONSE_OK:
                if os.path.exists(decode_filename(dialog.get_filename())):
                    if not dialog_yesno(_("File exists. Overwrite?")):
                        continue
                try:
                    new_name = decode_filename(dialog.get_filename())
                    self.instance_dict[new_name] = self.instance_dict[self.get_idict_key()]
                    del self.instance_dict[self.get_idict_key()]
                    self.m_filename = new_name
                    self.save()
                    self.set_title(self.m_filename)
                except IOError, e:
                    dialog_ok(_("Error saving file"), self, str(e), gtk.MESSAGE_ERROR)
                    dialog.destroy()
                    return False
                break
            elif ret in (gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT):
                break
        dialog.destroy()
        return ret == gtk.RESPONSE_OK
    def on_save(self, widget=None):
        """
        Return True if the file was saved, False if not.
        """
        if not self.m_filename:
            retval = self.on_save_as(widget)
        else:
            try:
                self.save()
                retval = True
            except IOError, e:
                dialog_ok(_("Error saving file"), self, str(e), gtk.MESSAGE_ERROR)
                retval = False
        if retval:
            self.m_savetime = time.time()
        return retval
    def new_file(self, action=None):
        """
        Return the new dialog window.
        """
        m = self.__class__()
        m.show_all()
        return m
    def select_empty_directory(self, title):
        msg = _("Select an empty directory, since we want to fill it with files.")
        dialog = gtk.FileChooserDialog(title,
            self, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
             gtk.STOCK_OK, gtk.RESPONSE_OK))
        label = gtk.Label(msg)
        label.show()
        dialog.vbox.pack_start(label, False, False)
        while 1:
            res = dialog.run()
            if res in (gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT):
                dialog.destroy()
                return
            elif res == gtk.RESPONSE_OK:
                if os.listdir(decode_filename(dialog.get_filename())):
                    msg_dlg = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
                        gtk.MESSAGE_INFO, gtk.BUTTONS_OK, msg)
                    msg_dlg.run()
                    msg_dlg.destroy()
                else:
                    break
        ret = decode_filename(dialog.get_filename())
        dialog.destroy()
        return ret


class LogWidget(gtk.ScrolledWindow):
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.g_textbuffer = gtk.TextBuffer()
        self.g_textbuffer.create_tag('h1', weight=pango.WEIGHT_BOLD,
            size=16*pango.SCALE)
        self.g_textview = gtk.TextView(buffer=self.g_textbuffer)
        self.add(self.g_textview)
    def write(self, s, tag=None):
        if tag:
            self.g_textbuffer.insert_with_tags_by_name(
                self.g_textbuffer.get_end_iter(),
                s,
                tag)
        else:
            self.g_textbuffer.insert(self.g_textbuffer.get_end_iter(), s)
        self.g_textview.scroll_to_iter(self.g_textbuffer.get_end_iter(), 0)
        # This is needed to make the window update:
        while gtk.events_pending():
            gtk.main_iteration()
    def popen(self, *args, **kwargs):
        """
        Return the Popen objects .returncode
        """
        self.write("$ %s\n" % " ".join(args[0]))
        p = osutils.Popen(
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            *args, **kwargs)
        while 1:
            p.poll()
            # returncode != None means that the process has finished
            if p.returncode != None:
                break
            while 1:
                s = p.stdout.readline()
                if not s:
                    break
                self.write(s)
            time.sleep(1)
        p.wait()
        return p.returncode


class LogWindow(gtk.Window):
    def __init__(self, parent):
        gtk.Window.__init__(self)
        self.set_transient_for(parent)
        self.set_destroy_with_parent(True)
        self.set_modal(True)
        vbox = gtk.VBox()
        vbox.set_spacing(4)
        self.add(vbox)
        self.set_default_size(630, 400)
        self.g_logwidget = LogWidget()
        vbox.pack_start(self.g_logwidget)
        vbox.pack_start(gtk.HSeparator(), False, False)
        bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_END)
        vbox.pack_start(bbox, False, False)
        self.g_close_button = gtk.Button(stock="gtk-close")
        self.g_close_button.set_sensitive(False)
        self.g_close_button.connect('clicked', lambda w: self.destroy())
        bbox.pack_start(self.g_close_button)
        self.show_all()
        self.write = self.g_logwidget.write
        self.popen = self.g_logwidget.popen
    def run_finished(self):
        self.g_close_button.set_sensitive(True)


class ClickableLabel(gtk.LinkButton):
    def __init__(self, label):
        """
        We are abusing the Link button by not giving it a real uri.
        So let ut not even pretend to follow its api.
        """
        gtk.LinkButton.__init__(self, label, label)
        self.get_children()[0].set_alignment(0.0, 0.5)
    def add_heading(self, text):
        def set_alignment(x, y):
            for c in self.get_children()[0].get_children():
                super(gtk.Label, c).set_alignment(x, y)
        vbox = gtk.VBox()
        vbox.set_alignment = set_alignment
        b = gtk.Label()
        b.set_markup(u"%s" % text)
        b.set_alignment(0.0, 0.5)
        vbox.pack_start(b, False)
        self.get_children()[0].reparent(vbox)
        self.add(vbox)
    def make_warning(self):
        im = gtk.Image()
        im.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_MENU)
        self.set_image(im)
        self.set_alignment(0.0, 0.5)


class ExceptionDialog(gtk.Dialog):
    def __init__(self, exception):
        gtk.Dialog.__init__(self, sys.exc_info()[0].__name__)
        self.set_resizable(True)
        self.set_border_width(6)
        self.set_has_separator(False)
        self.vbox.set_spacing(0)
        hbox = gtk.HBox()
        hbox.set_spacing(12)
        hbox.set_border_width(6)
        self.vbox.pack_start(hbox, False)
        vbox = gtk.VBox()
        hbox.pack_start(vbox, False, False)
        img = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_DIALOG)
        vbox.pack_start(img, False, False)
        vbox = gtk.VBox()
        hbox.pack_start(vbox)
        self.msg_vbox = gtk.VBox()
        vbox.pack_start(self.msg_vbox)
        self.g_primary = gtk.Label()
        if sys.exc_info()[0].__name__ == 'AttributeError':
            self.g_primary.set_name("DEBUGWARNING")
        self.g_primary.set_alignment(0.0, 0.5)
        self.g_primary.set_line_wrap(True)
        self.m_primary_bold = False
        self.msg_vbox.pack_start(self.g_primary)
        if isinstance(exception, StandardError):
            self.g_primary.set_text(str(exception).decode(sys.getfilesystemencoding(), 'replace'))
        else:
            if 'args' in dir(exception) and exception.args:
                estr = exception.args[0]
            else:
                estr = exception
            if not isinstance(estr, unicode):
                estr = str(estr).decode(sys.getfilesystemencoding(), 'replace')
            self.g_primary.set_text(estr)
            if 'args' in dir(exception):
                for s in exception.args[1:]:
                    self.add_text(s)
        # This label is here just for spacing
        l = gtk.Label("")
        vbox.pack_start(l)
        expander = gtk.Expander("Traceback")
        self.vbox.pack_start(expander)
        l = gtk.Label("".join(traceback.format_exception(
            sys.exc_type, sys.exc_value, sys.exc_traceback)).decode(sys.getfilesystemencoding(), 'replace'))
        l.set_alignment(0.0, 0.5)
        sc = gtk.ScrolledWindow()
        sc.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sc.set_size_request(-1, 100)
        expander.add(sc)
        sc.add_with_viewport(l)
        l = gtk.Label(_("Visit http://www.solfege.org/support if you need help."))
        l.set_alignment(0.0, 0.5)
        vbox.pack_start(l, False)
        w = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        self.set_default_response(gtk.RESPONSE_CLOSE)
        self.set_focus(w)
        self.show_all()
    def _make_primary_bold(self):
        if not self.m_primary_bold:
            self.m_primary_bold = True
            self.g_primary.set_markup('<span weight="bold" size="larger">%s</span>' %
                escape(self.g_primary.get_text()))
    def _parsep(self):
        l = gtk.Label("")
        l.show()
        self.msg_vbox.pack_start(l)
    def add_text(self, text):
        self._make_primary_bold()
        self._parsep()
        # We add a empty string with a newline to get the spacing
        l = gtk.Label(text)
        l.set_line_wrap(True)
        l.set_alignment(0.0, 0.5)
        l.show()
        self.msg_vbox.pack_start(l)
    def add_nonwrapped_text(self, text):
        self._make_primary_bold()
        self._parsep()
        sc = gtk.ScrolledWindow()
        l = gtk.Label()
        l.set_markup('<span font_family="monospace">%s</span>' % escape(text))
        l.set_line_wrap(False)
        l.set_alignment(0.0, 0.5)
        l.show()
        sc.add_with_viewport(l)
        self.msg_vbox.pack_start(sc)
        sc.show_all()
        sc.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        w, h = l.get_ancestor(gtk.Viewport).size_request()
        max_lines = 5
        lines = text.count("\n") + 1
        # This is the space the horizontal scrollbar takes
        scrollbar_height = (sc.get_hscrollbar().size_request()[1]
            + sc.style_get_property("scrollbar-spacing"))
        if lines <= max_lines:
            # make the scrollwin so high that it can display all lines
            sc.set_size_request(-1, h)
        else:
            sc.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sc.set_size_request(-1, int(h * max_lines / lines))
        adj = sc.get_hscrollbar().get_adjustment()
        def f(scrollbar, event):
            sc.set_size_request(-1, int(h * max_lines / lines) + scrollbar_height)
            scrollbar.disconnect(self._hscroll_expose_id)
        # f is called if the horizontal scrollbar is visible. This because we
        # need to allocate space for the scrollbar too.
        self._hscroll_expose_id = sc.get_hscrollbar().connect('expose-event', f)

def display_exception_message(exception, lessonfile=None):
        """Call this function only inside an except clause."""
        sourcefile, lineno, func, code = traceback.extract_tb(sys.exc_info()[2])[0]
        # We can replace characters because we will only display the
        # file name, not open the file.
        sourcefile = sourcefile.decode(sys.getfilesystemencoding(), 'replace')
        m = ExceptionDialog(exception)
        if lessonfile:
            m.add_text(_("Please check the lesson file %s.") % lessonfile)
        if sourcefile:
            m.add_text(_('The exception was caught in\n"%(filename)s", line %(lineno)i.') % {'filename': sourcefile, 'lineno': lineno})
        if 'm_nonwrapped_text' in dir(exception):
            m.add_nonwrapped_text(exception.m_nonwrapped_text)
        m.run()
        m.destroy()

