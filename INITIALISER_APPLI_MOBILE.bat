@echo off
chcp 65001 >nul
title Initialisation app mobile — Système PTP
cd /d "%~dp0"

echo.
echo  Ce script envoie les 14 écoles vers Supabase
echo  pour que l'application mobile affiche les données.
echo.
python initialiser_supabase.py
pause
