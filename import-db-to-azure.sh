#!/bin/bash

# Script d'importation de la base de données SQL vers Azure MySQL
# Ce script importe ecommerce_backup.sql vers votre serveur Azure MySQL

echo "🗄️  Import de la base de données vers Azure MySQL"
echo "================================================"

# Configuration de la base de données Azure (depuis AZURE_DEPLOYMENT_GUIDE.md)
DB_SERVER="flam-server.mysql.database.azure.com"
DB_USER="Flamingo"
DB_PASSWORD="Fl@mingo_237*"
DB_NAME="ecommerce"  # Nom de votre base de données
BACKUP_FILE="ecommerce_backup.sql"

echo "📋 Configuration détectée:"
echo "   Serveur: $DB_SERVER"
echo "   Utilisateur: $DB_USER"
echo "   Base de données: $DB_NAME"
echo "   Fichier de sauvegarde: $BACKUP_FILE"
echo ""

# Vérifier si le fichier de sauvegarde existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Erreur: Le fichier $BACKUP_FILE n'existe pas"
    echo "💡 Vérifiez que le fichier de sauvegarde est présent dans le répertoire"
    exit 1
fi

echo "✅ Fichier de sauvegarde trouvé"
echo ""

# Fonction pour créer un fichier de configuration MySQL
create_mysql_config() {
    cat > .mysql_config << EOF
[client]
host=$DB_SERVER
user=$DB_USER
password=$DB_PASSWORD
default-auth=mysql_native_password
ssl-mode=REQUIRED
EOF
    chmod 600 .mysql_config
    echo "✅ Fichier de configuration MySQL créé"
}

# Fonction pour tester la connexion avec différentes méthodes
test_connection() {
    echo "🔐 Test de connexion à Azure MySQL..."

    # Méthode 1: Avec fichier de configuration
    if mysql --defaults-file=.mysql_config -e "SELECT 1 as test;" 2>/dev/null; then
        echo "✅ Connexion réussie avec fichier de configuration"
        return 0
    fi

    # Méthode 2: SSL avec caching_sha2_password
    if mysql -h "$DB_SERVER" -u "$DB_USER" -p"$DB_PASSWORD" --ssl-mode=REQUIRED --default-auth=caching_sha2_password -e "SELECT 1;" 2>/dev/null; then
        echo "✅ Connexion réussie avec caching_sha2_password"
        export MYSQL_AUTH="--ssl-mode=REQUIRED --default-auth=caching_sha2_password"
        return 0
    fi

    # Méthode 3: Force SSL sans plugin spécifique
    if mysql -h "$DB_SERVER" -u "$DB_USER" -p"$DB_PASSWORD" --ssl-mode=REQUIRED -e "SELECT 1;" 2>/dev/null; then
        echo "✅ Connexion réussie avec SSL forcé"
        export MYSQL_AUTH="--ssl-mode=REQUIRED"
        return 0
    fi

    # Méthode 4: Via Azure CLI (fallback)
    echo "🔄 Tentative de connexion via Azure CLI..."
    if command -v az &> /dev/null; then
        echo "   Utilisation d'Azure CLI comme alternative..."
        return 2
    fi

    return 1
}

# Vérifier si mysql client est installé
if ! command -v mysql &> /dev/null; then
    echo "❌ Erreur: MySQL client n'est pas installé"
    echo "💡 Installation sur macOS: brew install mysql-client"
    echo "💡 Installation sur Ubuntu: sudo apt-get install mysql-client"
    echo "💡 Installation sur CentOS: sudo yum install mysql"
    exit 1
fi

echo "✅ MySQL client détecté"
echo ""

# Créer la configuration MySQL
create_mysql_config

# Tester la connexion
test_result=$(test_connection)
connection_status=$?

if [ $connection_status -eq 0 ]; then
    echo "$test_result"
elif [ $connection_status -eq 2 ]; then
    echo "ℹ️  Utilisation d'Azure CLI pour l'import"
    USE_AZURE_CLI=true
else
    echo "❌ Impossible de se connecter à Azure MySQL"
    echo "💡 Vérifications à faire:"
    echo "   1. Les règles de firewall Azure autorisent votre IP ✅"
    echo "   2. Les credentials sont corrects"
    echo "   3. Le serveur MySQL est démarré"
    echo "   4. Problème de compatibilité avec MySQL client 9.3.0"
    echo ""
    echo "🔧 Solutions alternatives:"
    echo "1. Installer MySQL client 8.0:"
    echo "   brew uninstall mysql"
    echo "   brew install mysql@8.0"
    echo "   echo 'export PATH=\"/opt/homebrew/opt/mysql@8.0/bin:\$PATH\"' >> ~/.zshrc"
    echo ""
    echo "2. Utiliser Azure CLI pour l'import (plus lent mais fonctionne):"
    echo "   Voulez-vous continuer avec Azure CLI? (o/n)"
    read -r use_cli
    if [[ $use_cli == "o" || $use_cli == "oui" ]]; then
        USE_AZURE_CLI=true
    else
        exit 1
    fi
fi

echo ""

# Créer la base de données si elle n'existe pas
echo "🏗️  Création de la base de données '$DB_NAME' si nécessaire..."

if [ "$USE_AZURE_CLI" = true ]; then
    # Utiliser Azure CLI
    az mysql flexible-server db create --resource-group E-Commerce --server-name flam-server --database-name "$DB_NAME" 2>/dev/null || echo "Base déjà existante ou créée"
else
    # Utiliser MySQL client
    mysql --defaults-file=.mysql_config -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || \
    mysql -h "$DB_SERVER" -u "$DB_USER" -p"$DB_PASSWORD" $MYSQL_AUTH -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
fi

if [ $? -eq 0 ]; then
    echo "✅ Base de données '$DB_NAME' prête"
else
    echo "❌ Erreur lors de la création de la base de données"
    exit 1
fi

echo ""

# Sauvegarder la base existante (par sécurité)
echo "💾 Sauvegarde de sécurité de la base existante..."
BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
SAFETY_BACKUP="azure_backup_before_import_$BACKUP_DATE.sql"

mysqldump -h "$DB_SERVER" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$SAFETY_BACKUP" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Sauvegarde de sécurité créée: $SAFETY_BACKUP"
else
    echo "⚠️  Impossible de créer une sauvegarde de sécurité (base vide?)"
fi

echo ""

# Analyser le fichier de sauvegarde
echo "🔍 Analyse du fichier de sauvegarde..."
TABLES_COUNT=$(grep -c "CREATE TABLE" "$BACKUP_FILE")
INSERT_COUNT=$(grep -c "INSERT INTO" "$BACKUP_FILE")
echo "   📊 Tables trouvées: $TABLES_COUNT"
echo "   📝 Instructions INSERT: $INSERT_COUNT"

# Vérifier la taille du fichier
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "   📁 Taille du fichier: $BACKUP_SIZE"
echo ""

# Demander confirmation
echo "⚠️  ATTENTION: Cette opération va:"
echo "   1. Importer les données de $BACKUP_FILE"
echo "   2. Remplacer les données existantes dans $DB_NAME"
echo "   3. Une sauvegarde de sécurité a été créée: $SAFETY_BACKUP"
echo ""
read -p "Voulez-vous continuer? (oui/non): " confirmation

if [[ $confirmation != "oui" && $confirmation != "o" && $confirmation != "yes" && $confirmation != "y" ]]; then
    echo "❌ Import annulé par l'utilisateur"
    rm -f .mysql_config
    exit 0
fi

echo ""
echo "🚀 Début de l'importation..."
echo "⏳ Cette opération peut prendre plusieurs minutes selon la taille des données"
echo ""

# Importer la base de données
if [ "$USE_AZURE_CLI" = true ]; then
    echo "📤 Import via Azure CLI (peut être plus lent)..."
    # Cette méthode nécessiterait un script plus complexe, utilisons MySQL avec SSL forcé
    mysql -h "$DB_SERVER" -u "$DB_USER" -p"$DB_PASSWORD" --ssl-mode=REQUIRED "$DB_NAME" < "$BACKUP_FILE"
else
    # Utiliser la méthode qui a fonctionné pour la connexion
    mysql --defaults-file=.mysql_config "$DB_NAME" < "$BACKUP_FILE" 2>/dev/null || \
    mysql -h "$DB_SERVER" -u "$DB_USER" -p"$DB_PASSWORD" $MYSQL_AUTH "$DB_NAME" < "$BACKUP_FILE"
fi

if [ $? -eq 0 ]; then
    echo "✅ Import terminé avec succès!"
    echo ""

    # Vérifier l'import
    echo "🔍 Vérification de l'import..."
    if [ "$USE_AZURE_CLI" = true ]; then
        IMPORTED_TABLES=$(mysql -h "$DB_SERVER" -u "$DB_USER" -p"$DB_PASSWORD" --ssl-mode=REQUIRED "$DB_NAME" -e "SHOW TABLES;" 2>/dev/null | wc -l)
    else
        IMPORTED_TABLES=$(mysql --defaults-file=.mysql_config "$DB_NAME" -e "SHOW TABLES;" 2>/dev/null | wc -l || \
                         mysql -h "$DB_SERVER" -u "$DB_USER" -p"$DB_PASSWORD" $MYSQL_AUTH "$DB_NAME" -e "SHOW TABLES;" | wc -l)
    fi
    echo "   📊 Tables importées: $((IMPORTED_TABLES - 1))"

    # Tester quelques tables critiques Django
    echo "   🧪 Test des tables critiques:"

    for table in "auth_user" "django_migrations" "store_product" "accounts_shopper"; do
        if [ "$USE_AZURE_CLI" = true ]; then
            COUNT=$(mysql -h "$DB_SERVER" -u "$DB_USER" -p"$DB_PASSWORD" --ssl-mode=REQUIRED "$DB_NAME" -e "SELECT COUNT(*) FROM $table;" 2>/dev/null | tail -n 1)
        else
            COUNT=$(mysql --defaults-file=.mysql_config "$DB_NAME" -e "SELECT COUNT(*) FROM $table;" 2>/dev/null | tail -n 1 || \
                   mysql -h "$DB_SERVER" -u "$DB_USER" -p"$DB_PASSWORD" $MYSQL_AUTH "$DB_NAME" -e "SELECT COUNT(*) FROM $table;" 2>/dev/null | tail -n 1)
        fi
        if [ $? -eq 0 ] && [ -n "$COUNT" ]; then
            echo "     ✅ $table: $COUNT enregistrements"
        else
            echo "     ⚠️  $table: table non trouvée ou erreur"
        fi
    done

    echo ""
    echo "🎉 Import de base de données terminé!"
    echo ""
    echo "📝 Prochaines étapes:"
    echo "1. 🔄 Mettre à jour les variables d'environnement Azure App Service:"
    echo "   DB_HOST=$DB_SERVER"
    echo "   DB_NAME=$DB_NAME"
    echo "   DB_USER=$DB_USER"
    echo "   DB_PASSWORD=$DB_PASSWORD"
    echo ""
    echo "2. 🚀 Redéployer l'application:"
    echo "   git add ."
    echo "   git commit -m 'Update database configuration'"
    echo "   git push origin main"
    echo ""
    echo "3. 🔄 Exécuter les migrations sur Azure (si nécessaire):"
    echo "   az webapp ssh --resource-group E-Commerce --name flam-ecommerce-1754047481"
    echo "   python manage.py migrate"

else
    echo "❌ Erreur lors de l'import"
    echo "💡 Vérifiez:"
    echo "   1. La syntaxe SQL du fichier de sauvegarde"
    echo "   2. Les permissions sur la base de données"
    echo "   3. L'espace disque disponible sur Azure"
    echo "   4. La compatibilité du client MySQL"
    exit 1
fi

# Nettoyer le fichier de configuration
rm -f .mysql_config

echo ""
echo "🧪 Pour tester la connexion manuellement:"
echo "mysql -h $DB_SERVER -u $DB_USER -p --ssl-mode=REQUIRED $DB_NAME"
