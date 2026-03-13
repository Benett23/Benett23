@echo off
chcp 65001 >nul
title Envoi emails — Système PTP
cd /d "%~dp0"

set PYTHON=
where py >nul 2>&1     && set PYTHON=py
if "%PYTHON%"=="" where python >nul 2>&1  && set PYTHON=python
if "%PYTHON%"=="" where python3 >nul 2>&1 && set PYTHON=python3

if "%PYTHON%"=="" (
    echo  Python introuvable. Installez Python depuis https://www.python.org/downloads/
    echo  Cochez "Add Python to PATH" pendant l'installation.
    pause
    exit /b 1
)

echo.
%PYTHON% envoyer_emails.py
pause
