#!/bin/bash

# Script de migration de base de données locale vers Azure MySQL
# Assurez-vous d'avoir exporté votre base de données depuis MySQL Workbench

echo "=== Migration de base de données vers Azure MySQL ==="

# Configuration Azure MySQL
AZURE_HOST="flam-server.mysql.database.azure.com"
AZURE_USER="Flamingo"
AZURE_PASSWORD="Fl@mingo_237*"
AZURE_DB="ecommerce_db"

# Chemin vers le client MySQL
export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"

echo "1. Vérification de la connexion à Azure MySQL..."
mysql -h $AZURE_HOST -u $AZURE_USER -p$AZURE_PASSWORD --ssl-mode=REQUIRED -e "SELECT 'Connexion réussie!' as status;"

if [ $? -eq 0 ]; then
    echo "✅ Connexion à Azure MySQL réussie!"
else
    echo "❌ Erreur de connexion à Azure MySQL"
    exit 1
fi

echo ""
echo "2. Listage des fichiers SQL disponibles..."
ls -la *.sql 2>/dev/null || echo "Aucun fichier .sql trouvé dans le répertoire courant"

echo ""
echo "Pour importer votre fichier SQL exporté depuis MySQL Workbench :"
echo "Utilisez la commande suivante (remplacez 'votre_fichier.sql' par le nom de votre fichier) :"
echo ""
echo "mysql -h $AZURE_HOST -u $AZURE_USER -p$AZURE_PASSWORD --ssl-mode=REQUIRED $AZURE_DB < votre_fichier.sql"
echo ""
echo "Exemple :"
echo "mysql -h $AZURE_HOST -u $AZURE_USER -p$AZURE_PASSWORD --ssl-mode=REQUIRED $AZURE_DB < ecommerce_backup.sql"
echo ""
echo "=== Fin du script de migration ==="
