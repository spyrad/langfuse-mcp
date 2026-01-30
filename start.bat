@echo off
cd /d "%~dp0"
call venv\Scripts\activate
uvicorn src.main:app --host localhost --port 8010 --reload
