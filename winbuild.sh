#!/bin/sh
PYVER=25
# This is used to select the prepackaged python tarball
MYPYVER=25
PYTHON=win32/bin/python.exe

setup() {
  # Step 1: Prepare the win32 directory. This is required both for
  # running from the source dir, and for the installer.
  rm win32 -rf
  mkdir win32
  mkdir win32/python
  (cd win32/python && tar zxf ../../../my-python-$MYPYVER.tgz)
  mv win32/python/DLLs win32/bin
  mv win32/python/Lib win32/bin
  mv win32/python/libs win32/bin
  mv win32/python/LICENSE.txt win32/LICENSE.python.txt
  mv win32/python/NEWS.txt win32/NEWS.python.txt
  mv win32/python/README.txt win32/README.python.txt
  mv win32/python/python.exe win32/bin
  mv win32/python/pythonw.exe win32/bin
  mv win32/python/w9xpopen.exe win32/bin
  mv win32/python/python25.dll win32/bin
  mv win32/python/msvcr71.dll win32/bin
  $PYTHON tools/get-gtk-files.py get-bundle
  $PYTHON tools/get-gtk-files.py unpack-bundle
  $PYTHON tools/get-gtk-files.py bin
  $PYTHON tools/get-gtk-files.py unpack
  mv win32/bin/libxml2.dll win32/bin/libxml2-2.dll
  mv win32/bin/libiconv2.dll win32/bin/iconv.dll

  echo '"lib/gtk-2.0/2.10.0/loaders/svg_loader.dll"' > win32/etc/gtk-2.0/gdk-pixbuf.loaders
  echo '"svg" 2 "gdk-pixbuf" "Scalable Vector Graphics" "LGPL"' >> win32/etc/gtk-2.0/gdk-pixbuf.loaders 
  echo '"image/svg+xml" "image/svg" "image/svg-xml" "image/vnd.adobe.svg+xml" "text/xml-svg" "image/svg+xml-compressed" ""' >> win32/etc/gtk-2.0/gdk-pixbuf.loaders 
  echo '"svg" "svgz" "svg.gz" ""' >> win32/etc/gtk-2.0/gdk-pixbuf.loaders 
  echo '" <svg" "*    " 100' >> win32/etc/gtk-2.0/gdk-pixbuf.loaders 
  echo '" <!DOCTYPE svg" "*             " 100' >> win32/etc/gtk-2.0/gdk-pixbuf.loaders 
  echo ' ' >> win32/etc/gtk-2.0/gdk-pixbuf.loaders
  # We did the above instead of using gdk-pixbuf-query-loaderse.exe because
  # we need to make a relocatable file.
  #win32/bin/gdk-pixbuf-query-loaders.exe win32/lib/gtk-2.0/2.10.0/loaders/svg_loader.dll > win32/etc/gtk-2.0/gdk-pixbuf.loaders 

  #mv win32/zlib-1.2.4/zlib1.dll win32/bin
  # Move these so CSound can find python25.dll
  cp -a ../pygtk-stuff/* win32/bin/lib/site-packages

  cp testgtkenv.bat testgtkenv.py win32/bin/
  echo "gtk-theme-name = \"MS-Windows\""  > win32/etc/gtk-2.0/gtkrc
  (cd win32 && find -name *.pyc | xargs rm)
}

build() {
  # Step 2: After this, we can run from the source dir
  # MS Windows have other defaults than linux. The 'sed' I have installed on
  # my windows machine don't support the -i option.
  mv default.config tmp.cfg
  sed -e "s/type=external-midiplayer/type=sequencer-device/" -e "s/csound=csound/csound=AUTODETECT/" -e "s/mma=mma/mma=AUTODETECT/" tmp.cfg > default.config
  rm tmp.cfg
  ./configure PYTHON=win32/bin/python.exe --disable-pygtk-test --enable-winmidi
  # we build the "all" target, and not the default one that rebuilds
  # some generated user manual .ly files because gettext.GNUTranslations
  # on my windows machine cannot read the .mo files.
  PATH=win32/bin:$PATH make PYTHONPATH=win32/bin/lib/site-packages/gtk-2.0 skipmanual=yes PYTHON_INCLUDES=-Iwin32/python/include all
  make winbuild
  cp README.txt INSTALL.win32.txt INSTALL.txt AUTHORS.txt COPYING.txt win32
}
install() {
  # Step 3: Install solfege into win32/ so that we can run from inside
  # it, or create the installer.
  find win32 -name "*.def" | xargs rm
  find win32 -name "*.a" | xargs rm
  find win32 -name "*.lib" | xargs rm
  $PYTHON tools/trim_win32_installer.py
  rm -rf win32/python
  PATH=win32/bin:$PATH make PYTHONPATH=win32/bin/lib/site-packages/gtk-2.0 DESTDIR=win32 prefix="" install skipmanual=yes PYTHON_INCLUDES=-Iwin32/python/includee
  (cp solfege/soundcard/winmidi.pyd win32/share/solfege/solfege/soundcard)
  cp win32-start-solfege.pyw win32/bin
  cp solfegedebug.bat win32/bin/
}


mk_pygtk_stuff() {
  rm -rf ../pygtk-stuff
  mkdir ../pygtk-stuff
  cp /C/Python$PYVER/Lib/site-packages/pygtk.* ../pygtk-stuff/
  cp -a /C/Python$PYVER/Lib/site-packages/cairo/ ../pygtk-stuff/
  cp -a /C/Python$PYVER/Lib/site-packages/gtk-2.0/ ../pygtk-stuff/
}
 

if test "x$1" = "xsetup"; then
  setup
fi
if test "x$1" = "xbuild"; then
  build
fi
if test "x$1" = "xinstall"; then
  install
fi
if test "x$1" = "xbuildenv"; then
  mk_pygtk_stuff
fi
if test "x$1" = "xgo"; then
  setup
  build
  install
fi
if test "x$1" = "x-h"; then
  echo "sub commands:"
  echo "   buildenv      create ../pygtk-stuff/  This has to be done once with"
  echo "                 the pygtk binary installer package installed."
  echo "   setup         Create the win32/ directory that includes all deps."
  echo "   build         Build the package. After this we can run from"
  echo "                 the source directory."
  echo "   install       Install into win32/ directory."
  echo "   go            run setup-build-install."
fi

