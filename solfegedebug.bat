@echo off
rem GNU Solfege - free eartraining
rem Copyright (C) 2008, 2009  Tom Cato Amundsen
rem

echo PYTHONHOME must not point to locally installed python, for example
echo C:\Python25 or D:\Python25
echo Current value:
echo PYTHONHOME=%PYTHONHOME%

if exist configure.ac goto infomsg

:runsolfege
set GDK_PIXBUF_MODULE_FILE=../../etc/gtk-2.0/gdk-pixbuf.loaders
python.exe solfege --debug
goto end
:infomsg
echo.
echo This script should only be run when installed into the win32 folder
echo or after the generated installer is installed.
echo If you want to run Solfege from the source directory without installing,
echo then you should run runsrcdir.bat
echo.
:end
pause
