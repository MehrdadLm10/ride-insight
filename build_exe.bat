@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3.11 -m venv .venv
  if errorlevel 1 goto failed
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install "pyinstaller>=6,<7"
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --windowed --name RideInsight --collect-all playwright app.py
if errorlevel 1 goto failed
echo Done. Run dist\RideInsight\RideInsight.exe
echo Distribute the WHOLE dist\RideInsight folder, not just its exe.
pause
exit /b 0
:failed
echo Build failed. Copy the error above.
pause
exit /b 1
