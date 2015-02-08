Table of Contents
*****************

1 GNU Solfege 3.22.2
  1.1 Requirements
    1.1.1 MS Windows
    1.1.2 GNU/Linux and the rest of us
      1.1.2.1 Runtime
      1.1.2.2 Build dependencies
  1.2 Versioning
  1.3 Internationalization
  1.4 Sound issues
    1.4.1 `--no-sound' command line option
    1.4.2 Missing `/dev/music'
  1.5 If it just won't work
  1.6 History
  1.7 Copyright notice


1 GNU Solfege 3.22.2
********************

Solfege is a free ear training program written in python using gtk+ and
PyGTK.  Solfege is expected to work on any OS where python, gtk+ and
pygtk are ported, but some adjustments might be necessary.

Check out the latest news and precompiled binaries at
`http://www.solfege.org'. Get the source code for the stable releases
at `ftp://ftp.gnu.org/gnu/solfege' and bleeding edge at
`ftp://alpha.gnu.org/gnu/solfege'.

   Ear training is a big subject with many connections to music theory
and performance of music, so I won't even try to make "a complete
computer based ear training course". To use this software, you need some
basic knowledge about music theory.

   As of 18 June 2000, Solfege is an official part of the GNU project.
Visit `http://www.gnu.org' for more info.

1.1 Requirements
================

Most of this software are usually included with your linux distro.  But
sometimes you have to use a quite new and uptodate linux distribution
because solfege require quite new versions of them. A good alternative
can then be to try one of the older stable releases. We try to collect
OS specific information on the wiki at `http://www.solfege.org/wiki'.
But this depends on users contributing their data.

1.1.1 MS Windows
----------------

MS Windows users can download the installer program
(solfege-win32-3.22.2.exe) that contains everything they need.

1.1.2 GNU/Linux and the rest of us
----------------------------------

The rest of us should check that the following is installed:

1.1.2.1 Runtime
...............

   * Python >= 2.5

   * Gtk+ >= 2.12

   * PyGTK >= 2.12 (Debian: python-gtk2)

   * Midi working on /dev/music or /dev/sequencer (for example using
     OSS or ALSA with OSS emulation). Or at least possible to play midi
     files on some external program. It seems that your soundcard must
     support FM-synthesis or wavetable synthesis to use /dev/music or
     /dev/sequencer. If it does not, you need to do that in software,
     for example using timidity. Please check
     http://www.solfege.org/Solfege/SoundSetup . I try to update it
     more often than this file. And everybody is allowed to edit that
     page.

1.1.2.2 Build dependencies
..........................

   * GNU Make

   * Gettext

   * Python header files. (The RedHat package is called python-devel.)

   * C compiler (only GCC is tested, nothing else is expected to work.)

   * GNU texinfo (ftp://ftp.gnu.org/gnu/texinfo)

   If you get the program fresh from the bzr repository, then you also
need need:

   * swig 1.1 or 1.3 (Simplified Wrapper and Interface Generator) found
     at `http://www.swig.org'.

   * GNU Lilypond 2.10 or 2.12. Newer version might work.
     (`http://www.lilypond.org')

   * xsltproc and docbook

   * xml2po

   * txt2man

   If you edit `configure.ac', you need GNU Autoconf.

1.2 Versioning
==============

Solfege uses a versioning scheme similar to the Linux kernel.  In a
version "x.y.z", an even (0, 2, 4, 6, 8) second number 'y' denotes a
stable version. So releases called 1.0, 1.2.2, 2.0.0 and similar should
work as documented, while a release versioned 1.1.3 or 1.9.2 is a test
release that is expected to cause some troubles (that should be
reported to solfege-devel@lists.sourceforge.net).

1.3 Internationalization
========================

You get translated messages the same ways as with most GNU programs, by
setting environment variables. On a recent linux distribution the
correct environment variables are set, and solfege will show messages
in your language, if translations exist. Set the LANGAUGE environment
variable to change this from the command line:

       export LANGUAGE=sv
       solfege

   Please notice that if you mess with many of the LC_XXX variables,
then you might see the following error message on the console:

     Traceback (most recent call last):
       File "./solfege.py", line 51, in ?
         src.i18n.setup(".", src.cfg.get_string("app/lc_messages"))
       File "./src/i18n.py", line 63, in setup
         locale.setlocale(locale.LC_ALL, '')
       File "/usr/lib/python2.4/locale.py", line 381, in setlocale
         return _setlocale(category, locale)
     locale.Error: unsupported locale setting

   Solfege will recover from this error and run without translated
messages.  It is not a bug in GNU Solfege if you see this message. Your
environment variables are wrong or you have forgotten to run some
locale related update command like `locale-gen' or similar. If you want
to change the language by setting environment variables, you should set
LANGUAGE and not LC_ALL.

   You can also select the language to use from the preferences window
of the program.

   Please read `http://www.solfege.org/Solfege/TranslateSolfege' if you
want to help the translation.

1.4 Sound issues
================

You configure how Solfege should play sounds from the preferences
window available from the File menu.

   Be aware that it seems like your soundcard must support FM-synthesis
or wavetable synthesis to work out of the box. One card I know that
does this is SoundBlaster Live. If it does not, you need to emulate
this in software, for example by using timidity as an external
midiplayer.  More info on `http://www.solfege.org/Solfege/SoundSetup'.

1.4.1 `--no-sound' command line option
--------------------------------------

If you plan to play sounds using an external midiplayer, or if you get
other error messages that you think might be caused by your sound setup
or Solfeges sound code, then you should start the program with the
`--no-sound' command line option the first time you run the program,
and then configure sound from the preferences window.

1.4.2 Missing `/dev/music'
--------------------------

If you have a recent linux kernel (at least late 2.2.x and newer,
someone please confirm when /dev/music was added...) but `/dev/music'
is missing, you can probably create the device file yourself with
MAKEDEV or `mknod /dev/music u 14 8' as root.

1.5 If it just won't work
=========================

See the INSTALL file if you have problems building and installing
Solfege, and check the man page or run the program with the '--help'
command line option for a list of command line options.

   You are welcome to ask questions on
<solfege-devel@lists.sourceforge.net> if this documentation and
`http://www.solfege.org' does not give you an answer.

1.6 History
===========

The first versions of Solfege was written in the first quarter of 1999
when I studied my 4th and last year at Malmö Academy of Music.  I was
writing a "special subject" (what is the english term??) about ear
training and used GNU Lilypond and LaTeX to typeset the paper.

   I accidentally browsed the "help needed" page at the GNU web site
when I saw they needed someone to write an ear training program for
music students.

   In the beginning I was experimenting with wxWindows, a cross
platform C++ GUI toolkit, but luckily, at some point I found the python
bindings for gtk+ and have never looked back.

1.7 Copyright notice
====================

Copyright (C) 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008 Tom
Cato Amundsen

   This if free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation; either version 2.

   This is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

   You should have received a copy of the GNU General Public License
with your Debian GNU/Linux system, in /usr/doc/copyright/GPL, with the
solfege source package as the file COPYING and available in the online
help system..  If not, write to the Free Software Foundation, Inc., 51
Franklin ST, Fifth Floor, Boston, MA  02110-1301  USA

   Tom Cato Amundsen <tca@gnu.org>

