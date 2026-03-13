@echo off
chcp 65001 >nul
title Envoi emails — Système PTP
cd /d "%~dp0"

echo.
python envoyer_emails.py
pause
