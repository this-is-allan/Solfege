# GNU Solfege - free ear training
# Copyright (C) 2009, 2011 Tom Cato Amundsen

import sys
print sys.version

import gtk
print gtk
print gtk.ver

class Win(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_default_size(600, 400)
        b = gtk.Button("Click to quit")
        b.connect('clicked', gtk.main_quit)
        self.add(b)

w = Win()
w.show_all()
gtk.main()
