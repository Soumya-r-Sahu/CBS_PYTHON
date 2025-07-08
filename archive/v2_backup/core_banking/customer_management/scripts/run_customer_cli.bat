@echo off
REM Run Customer Management CLI Interface for CBS_PYTHON

echo Starting Customer Management CLI Interface...
echo.

REM Set Python path to include project root
set PYTHONPATH=%PYTHONPATH%;%~dp0..\..\..\..

REM Parse command-line arguments
set args=%*

REM Run the Customer Management CLI interface
python -m core_banking.customer_management.presentation.cli.customer_management_cli %args%

echo.
echo Customer Management CLI Interface completed.
