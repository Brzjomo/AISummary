@echo off
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" aisummary
@REM call pip install pydub
python tts.py

pause
