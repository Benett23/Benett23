@echo off
chcp 65001 >nul
title Système PTP — Chris Gnabroyou
cd /d "%~dp0"

echo.
echo  Mise à jour du code...
git pull origin claude/ptp-multi-agent-system-WdHPE 2>nul

echo.
echo  Vérification des dépendances...
pip install -r requirements.txt -q

echo.
python lancer.py
pause
