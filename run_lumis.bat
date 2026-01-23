@echo off
setlocal

echo [Lumis] Checking environment...

if not exist venv (
    echo [Lumis] Creating virtual environment...
    python -m venv venv
)

echo [Lumis] Checking dependencies...
rem Install customtkinter and others
venv\Scripts\pip install -r requirements.txt --quiet --disable-pip-version-check

echo [Lumis] Launching Native App...
rem Use python (console visible for debug) or pythonw (hidden)
venv\Scripts\python gui_app.py
