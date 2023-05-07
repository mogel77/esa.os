@echo off
mode 131,36
python.exe -m pip install --upgrade pip
pip install windows-curses
pip install watchdog
pip install requests
python esaos.py
pause

