@echo off
chcp 65001 >nul
title Système PTP — Chris Gnabroyou
cd /d "%~dp0"

echo.
echo  Mise à jour du code...
git pull origin claude/ptp-multi-agent-system-WdHPE 2>nul

echo.

:: Trouver Python (py, python, python3)
set PYTHON=
where py >nul 2>&1     && set PYTHON=py
if "%PYTHON%"=="" where python >nul 2>&1  && set PYTHON=python
if "%PYTHON%"=="" where python3 >nul 2>&1 && set PYTHON=python3

if "%PYTHON%"=="" (
    echo  ============================================================
    echo   ERREUR : Python n'est pas installe ou pas dans le PATH.
    echo  ============================================================
    echo.
    echo  Solution :
    echo   1. Allez sur https://www.python.org/downloads/
    echo   2. Telechargez Python 3.11 ou plus recent
    echo   3. IMPORTANT : cochez "Add Python to PATH" pendant l'install
    echo   4. Relancez ce fichier .bat
    echo.
    pause
    exit /b 1
)

echo  Python trouve : %PYTHON%
echo.
echo  Installation des dependances...
%PYTHON% -m pip install -r requirements.txt -q

echo.
%PYTHON% lancer.py
pause
