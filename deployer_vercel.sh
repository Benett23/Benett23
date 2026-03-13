#!/bin/bash
# Déploiement PWA sur Vercel
# Usage : bash deployer_vercel.sh

set -e

# Charger le token depuis .env
export $(grep VERCEL_TOKEN .env | xargs)

if [ -z "$VERCEL_TOKEN" ]; then
  echo "❌ VERCEL_TOKEN manquant dans .env"
  exit 1
fi

echo "🚀 Déploiement vers Vercel..."
cd pwa
vercel --token "$VERCEL_TOKEN" --prod --yes

echo ""
echo "✅ Déploiement terminé !"
echo "   Ouvre l'URL affichée ci-dessus dans Safari (iPhone) pour installer la PWA."
