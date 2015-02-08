# GNU Solfege - free ear training software
# Copyright (C) 2005, 2007, 2008, 2011  Tom Cato Amundsen
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
"""
This file does the checking for optional features that depend on
python modules the user can have installed.

It also does sanity check on the python and pygtk versions and some
other initial setup tasks.
"""

import sys
import os
import textwrap

def assert_python_version(required_version):
    if sys.version_info < required_version:
        sys.exit("Solfege need Python %s or newer. The configure script told you so.\nThis is Python %s" % (".".join([str(i) for i in required_version]), sys.version))

def setup_pygtk(required_version):
    import pygtk
    # this is needed for py2exe
    if sys.platform == 'win32':
        os.environ['PATH'] += ";lib;bin;"
    else:
        pygtk.require("2.0")
    import gtk
    gtk.rc_parse("solfege.gtkrc")
    # The rest of this function is just for sanity check. Not really required.
    if gtk.pygtk_version < required_version:
        sys.exit("\n" + "\n ".join(textwrap.wrap(" GNU Solfege requires pygtk version %s or newer. The version installed appears to be %s. Exiting program." % (
            ".".join([str(i) for i in required_version]),
            ".".join([str(i) for i in gtk.pygtk_version])))))

def init(options):
    assert_python_version((2, 5))
    setup_pygtk((2, 12))

