
dnl a macro to check for ability to create python extensions
dnl  AM_CHECK_PYTHON_HEADERS([ACTION-IF-POSSIBLE], [ACTION-IF-NOT-POSSIBLE])
dnl function also defines PYTHON_INCLUDES
AC_DEFUN([AM_CHECK_PYTHON_HEADERS],
[AC_REQUIRE([AM_PATH_PYTHON])
AC_MSG_CHECKING(for headers required to compile python extensions)
dnl deduce PYTHON_INCLUDES
py_prefix=`$PYTHON -c "import sys; print sys.prefix"`
py_exec_prefix=`$PYTHON -c "import sys; print sys.exec_prefix"`
PYTHON_INCLUDES="-I${py_prefix}/include/python${PYTHON_VERSION}"
if test "x$MSYSTEM" = "xMINGW32"; then
  PYTHON_INCLUDES="-I${py_prefix}/include"
fi
if test "$py_prefix" != "$py_exec_prefix"; then
  PYTHON_INCLUDES="$PYTHON_INCLUDES -I${py_exec_prefix}/include/python${PYTHON_VERSION}"
fi
AC_SUBST(PYTHON_INCLUDES)
dnl check if the headers exist:
save_CPPFLAGS="$CPPFLAGS"
CPPFLAGS="$CPPFLAGS $PYTHON_INCLUDES"
AC_TRY_CPP([#include <Python.h>],dnl
[AC_MSG_RESULT(found)
$1],dnl
[AC_MSG_RESULT(not found)
$2])
CPPFLAGS="$save_CPPFLAGS"
])

AC_DEFUN([BUGGY_DISTRO_CHECK_PYGNOME2],
 [
   dnl We have to write this extra test because redhat 8.0 don't
   dnl include gnome-python-2.0.pc in the gnome-python2 package.
   dnl
   dnl Since there are not gnome.pygnome_version variable, we import
   dnl gtk and gnome, and test only gtk.pygtk_version.
   dnl Yes, I know this is stupid!
   AC_MSG_CHECKING(extra test for pygnome >= 1.99.11)
   changequote(<<, >>)dnl
   prog="
import sys
try:
    import pygtk
    pygtk.require('2.0')
except:
    pass
try:
    import gtk, gnome
except:
    sys.exit(1)
if gtk.pygtk_version < (1, 99, 11):
    sys.exit(1)
sys.exit(0)"
    changequote([, ])dnl
    if $PYTHON -c "$prog" 0>&AC_FD_CC 2>&AC_FD_CC
then
AC_MSG_RESULT([[okay. (At least pygtk look ok.)]])
$1
    else
AC_MSG_ERROR(cannot find usable gnome-python)
$2
    fi
  ])

AC_DEFUN([MY_SWIG_TEST],
  [
  $SWIG -version > tmpswig 2&>tmpswig
  if grep "SWIG Version 2.0" tmpswig
  then
    [$1="2.0"]
  elif grep "SWIG Version 1.3" tmpswig
  then
    [$1="1.3"]
  elif grep "SWIG Version 1.1" tmpswig
  then
    [$1="1.1"]
  else
    [$1="unknown"]
  fi
  rm tmpswig
]
)

dnl Solfege requrie lilypond 2.10 or newer, and one command line option
dnl differ between 2.10 and newer releases. So we only need to see if we
dnl have 2.10.
AC_DEFUN([MY_LILYPOND_TEST],
  [
  $LILYPOND --version > tmplily 2&>tmplily
  if grep "GNU LilyPond 2.10." tmplily
  then
    [$1="2.10"]
  else
    [$1="unknown"]
  fi
  rm tmplily
]
)

AC_DEFUN([MY_PATH_PROG],
 [
  AC_PATH_PROG($1,$2)
if test -z $$1
then
  AC_MSG_ERROR([$2 not found. $3])
fi
 ]
)
