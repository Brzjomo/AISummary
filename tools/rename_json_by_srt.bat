@echo off
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" aisummary
python rename_json_by_srt.py

pause
