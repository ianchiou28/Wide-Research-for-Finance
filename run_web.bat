@echo off
chcp 65001 >nul
set PYTHONUTF8=1
python -X utf8 web_app.py
pause
