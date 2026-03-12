#!/bin/bash
# Configure le cron job pour envoyer les actualités IA chaque matin à 9h

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/ai_news.py"
LOG_PATH="$SCRIPT_DIR/ai_news.log"
PYTHON_BIN="$(which python3)"

CRON_JOB="0 9 * * * $PYTHON_BIN $SCRIPT_PATH >> $LOG_PATH 2>&1"

# Vérifie que le .env existe
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "⚠️  Fichier .env manquant. Copie .env.example vers .env et remplis-le :"
    echo "    cp $SCRIPT_DIR/.env.example $SCRIPT_DIR/.env"
    echo "    nano $SCRIPT_DIR/.env"
    exit 1
fi

# Ajoute le cron job s'il n'existe pas déjà
(crontab -l 2>/dev/null | grep -v "ai_news.py"; echo "$CRON_JOB") | crontab -

echo "✅ Cron job configuré : actualités IA envoyées par email tous les jours à 9h00"
echo "   Log : $LOG_PATH"
echo ""
echo "Pour vérifier : crontab -l"
echo "Pour tester maintenant : python3 $SCRIPT_PATH"
