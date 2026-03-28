@echo off
REM PRADYSAGI Installation Script (Windows)
REM Installs complete PRADYSAGI system with all dependencies

setlocal enabledelayedexpansion

REM Colors setup (Windows 10+)
for /F %%A in ('echo prompt $H ^| cmd') do set "BS=%%A"

echo.
echo ===============================================================
echo           PRADYSAGI Installation (Windows)
echo ===============================================================
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python 3.11+ from https://www.python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo OK: Python %PYTHON_VERSION% found

REM Create virtual environment
if not exist venv (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    echo OK: Virtual environment created
) else (
    echo OK: Virtual environment already exists
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
echo OK: pip upgraded

REM Install PRADYSAGI
echo.
echo Installing PRADYSAGI...
pip install -e . >nul 2>&1
if errorlevel 1 (
    echo ERROR: Installation failed
    pause
    exit /b 1
)
echo OK: PRADYSAGI installed

REM Install optional dependencies
echo.
echo Installing optional dependencies...
pip install rich click >nul 2>&1
echo OK: Optional dependencies installed

REM Verify installation
echo.
echo Verifying installation...
python -c "from pradysagican.core.integration import pradysagi" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Verification failed
    pause
    exit /b 1
)
echo OK: Installation verified

REM Create .env if not exists
if not exist .env (
    echo.
    echo Creating .env configuration file...
    (
        echo # PRADYSAGI Configuration
        echo MODE=hybrid
        echo ENABLE_RAG=true
        echo ENABLE_TOOLS=true
        echo HOST=0.0.0.0
        echo PORT=8000
        echo.
        echo # API Keys (optional - fill in if using cloud models^)
        echo # OPENAI_API_KEY=sk-...
        echo # ANTHROPIC_API_KEY=sk-ant-...
    ) > .env
    echo OK: .env configuration created
)

REM Summary
echo.
echo ===============================================================
echo                  Installation Complete!
echo ===============================================================
echo.
echo PRADYSAGI is ready to use!
echo.
echo Next steps:
echo.
echo   1. Start interactive chat:
echo      pradysagi chat
echo.
echo   2. Start API server:
echo      pradysagi server
echo.
echo   3. Check system status:
echo      pradysagi status
echo.
echo   4. Run configuration wizard:
echo      pradysagi configure
echo.
echo Documentation: https://github.com/prady/pradysagican
echo.

pause
