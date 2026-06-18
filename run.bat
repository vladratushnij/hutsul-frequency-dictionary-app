@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==============================================
echo   Hutsul Frequency Dictionary - launcher
echo ==============================================

rem --- 1. Find a working Python interpreter ---------------------------------
set "PYEXE="
where py >nul 2>nul && set "PYEXE=py -3"
if not defined PYEXE (
    where python >nul 2>nul && set "PYEXE=python"
)
if not defined PYEXE (
    where python3 >nul 2>nul && set "PYEXE=python3"
)
if not defined PYEXE (
    echo [ERROR] Python was not found.
    echo Install Python 3.10+ from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)
echo Using interpreter: %PYEXE%

rem --- 2. Create the virtual environment if needed --------------------------
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PYEXE% -m venv venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
)

set "VENVPY=venv\Scripts\python.exe"

rem --- 3. Install / update dependencies ------------------------------------
echo Checking dependencies...
"%VENVPY%" -m pip install --upgrade pip >nul 2>nul
"%VENVPY%" -c "import streamlit, pandas, openpyxl" >nul 2>nul
if errorlevel 1 (
    echo Installing dependencies from requirements.txt ...
    "%VENVPY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
)

rem --- 4. Launch the application -------------------------------------------
echo Starting Streamlit...
"%VENVPY%" -m streamlit run app.py

pause
endlocal
