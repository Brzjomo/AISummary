@echo off
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" aisummary
python json2pbf.py

pause
