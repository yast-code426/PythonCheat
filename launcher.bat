@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: PY_Cheat Professional Launcher v3.0
:: ============================================================

set "SCRIPT_DIR=%~dp0"
set "MAIN_SCRIPT=%SCRIPT_DIR%PY_Cheat.py"

:: Display Title
cls
echo.
echo  ========================================================================
echo.
echo     PPPP    Y    Y   CCCCC   H   H   EEEEE   AAAA   TTTTT
echo     P   P    Y Y     C       H   H   E       A   A    T
echo     PPPP      Y      C       HHHHH   EEEE    AAAAA    T
echo     P         Y      C       H   H   E       A   A    T
echo     P         Y      CCCCC   H   H   EEEEE   A   A    T
echo.
echo               Memory Editor Professional v3.0
echo.
echo  ========================================================================
echo.

:: Step 1: Check Python
echo [1/4] Checking Python environment...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo [INFO] Please download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VERSION=%%i
echo [OK] Python %PY_VERSION% detected.
echo.

:: Step 2: Check pip
echo [2/4] Checking pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] pip not found, installing...
    python -m ensurepip --default-pip >nul 2>&1
)
echo [OK] pip is available.
echo.

:: Step 3: Check dependencies
echo [3/4] Checking dependencies...
set "DEPS_OK=1"

python -c "import customtkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INSTALL] Installing customtkinter...
    python -m pip install customtkinter -q
)

python -c "import psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INSTALL] Installing psutil...
    python -m pip install psutil -q
)

python -c "import pymem" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INSTALL] Installing pymem...
    python -m pip install pymem -q
)

echo [OK] All dependencies are ready.
echo.

:: Step 4: Run the application
echo [4/4] Starting PY_Cheat...
echo.

if not exist "%MAIN_SCRIPT%" (
    echo [ERROR] PY_Cheat.py not found!
    echo [INFO] Expected location: %MAIN_SCRIPT%
    pause
    exit /b 1
)

python "%MAIN_SCRIPT%"
exit /b 0
