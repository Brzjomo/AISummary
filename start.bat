@echo off
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" aisummary
python -m streamlit run app.py

pause
