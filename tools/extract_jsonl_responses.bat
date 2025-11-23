@echo off
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" aisummary
python extract_jsonl_responses.py

pause
