@echo off
chcp 65001 >nul
title Initialisation app mobile — Système PTP
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
echo  Ce script envoie les 14 ecoles vers Supabase
echo  pour que l'application mobile affiche les donnees.
echo.
%PYTHON% initialiser_supabase.py
pause
