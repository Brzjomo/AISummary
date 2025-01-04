@echo off
call conda activate aisummary
python -m streamlit run app.py
pause