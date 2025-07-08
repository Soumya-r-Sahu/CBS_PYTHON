@echo off
REM Run Interactive Customer Management CLI Interface for CBS_PYTHON

echo Starting Interactive Customer Management CLI Interface...
echo.

REM Set Python path to include project root
set PYTHONPATH=%~dp0..\..\..\..

REM Parse command-line arguments
set args=%*

REM Change to the presentation/cli directory
cd %~dp0..\presentation\cli

REM Run the Interactive Customer Management CLI interface
python interactive_customer_cli.py %args%

echo.
echo Interactive Customer Management CLI Interface completed.
