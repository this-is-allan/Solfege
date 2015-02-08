rem GNU Solfege - free eartraining
rem Copyright (C) 2000, 2001, 2002, 2003, 2004, 2005  Tom Cato Amundsen

rem The contents of langenviron.bat is set by configwindow.py
rem and is used to select the language to use.

rem This script will launch Solfege from the source directory.
rem It will use the Python interpreter and all other deps from
rem the win32 directory
rem

IF EXIST "%APPDATA%\GNU Solfege\langenviron.bat" (call "%APPDATA%\GNU Solfege\langenviron.bat")

rem The following line is not necessary if gtk+ adds to the PATH, but we
rem do this just to be safe.
set PATH=win32\bin
win32\bin\python.exe solfege.py
pause
