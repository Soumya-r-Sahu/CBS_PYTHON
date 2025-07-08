@echo off
REM Run ATM CLI Interface for CBS_PYTHON

echo Starting ATM CLI Interface...
echo.

REM Set Python path to include project root
set PYTHONPATH=%PYTHONPATH%;%~dp0..\..\..\..

REM Run the ATM CLI interface
python -m digital_channels.atm-switch.presentation.cli.atm_interface

echo.
echo ATM CLI Interface closed.
