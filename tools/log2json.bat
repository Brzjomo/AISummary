@echo off
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" aisummary
python log2json.py

pause
