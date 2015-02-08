import os
import sys
from subprocess import Popen

sys.path.append("../share/solfege")
from solfege import winlang

lang = winlang.win32_get_langenviron()
if lang and (lang != 'system default'):
    os.environ['LANGUAGE'] = lang

os.environ['GDK_PIXBUF_MODULE_FILE'] = "../../etc/gtk-2.0/gdk-pixbuf.loaders"

# We need to set PYTHONHOME because if not, and the user has set it,
# we will run the users locally and maybe buggy python modules instead
# of the included ones.
os.environ['PYTHONHOME'] = os.getcwdu()
Popen([r"pythonw.exe", "solfege"] + sys.argv[1:])
