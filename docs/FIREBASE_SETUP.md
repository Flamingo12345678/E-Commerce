# Configuration Firebase pour l'authentification

## Étapes de configuration

### 1. Créer un projet Firebase

1. Allez sur [Firebase Console](https://console.firebase.google.com/)
2. Cliquez sur "Ajouter un projet"
3. Donnez un nom à votre projet (ex: "yee-ecommerce")
4. Suivez les étapes de création

### 2. Activer l'authentification

1. Dans votre projet Firebase, allez dans "Authentication"
2. Cliquez sur "Commencer"
3. Allez dans l'onglet "Sign-in method"
4. Activez les providers suivants :
   - **Google** : Activez et configurez avec votre email de support
   - **Facebook** : Activez et configurez avec votre App ID et App Secret Facebook

### 3. Configurer l'application web

1. Allez dans "Project Settings" (icône engrenage)
2. Scroll vers le bas et cliquez sur "Ajouter une app"
3. Sélectionnez "Web" (icône </>)
4. Donnez un nom à votre app (ex: "YEE Web App")
5. Activez "Firebase Hosting" si souhaité
6. Copiez la configuration qui s'affiche

### 4. Obtenir les clés de configuration

Dans les paramètres du projet, section "Vos applications", vous trouverez :

```javascript
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef..."
};
```

### 5. Configurer le SDK Admin (pour le backend)

1. Allez dans "Project Settings" → "Service Accounts"
2. Cliquez sur "Generate new private key"
3. Téléchargez le fichier JSON
4. Placez-le dans votre projet (ex: `firebase-credentials.json`)
5. **Important** : Ajoutez ce fichier à votre `.gitignore`

### 6. Configurer Facebook Login

1. Allez sur [Facebook Developers](https://developers.facebook.com/)
2. Créez une nouvelle app ou utilisez une existante
3. Ajoutez le produit "Facebook Login"
4. Dans les paramètres de Facebook Login :
   - Ajoutez votre domaine dans "Valid OAuth Redirect URIs"
   - Ex: `https://your-project.firebaseapp.com/__/auth/handler`
5. Copiez l'App ID et l'App Secret dans Firebase Authentication

### 7. Mise à jour du fichier .env

Mettez à jour votre fichier `.env` avec les vraies valeurs :

```env
# Firebase Configuration
FIREBASE_API_KEY=AIza...
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abcdef...
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
```

### 8. Domaines autorisés

Dans Firebase Authentication → Settings → Authorized domains, ajoutez :
- `localhost` (pour le développement)
- Votre domaine de production
- Votre domaine ngrok si utilisé

### 9. Test de l'intégration

1. Redémarrez votre serveur Django
2. Allez sur la page de connexion
3. Cliquez sur "Google" ou "Facebook"
4. Vérifiez que l'authentification fonctionne

## Sécurité

- Ne jamais commiter les fichiers de credentials Firebase
- Utilisez des variables d'environnement pour toutes les clés sensibles
- Configurez les règles de sécurité Firebase selon vos besoins
- Limitez les domaines autorisés en production

## Dépannage

### Erreur "auth/invalid-api-key"
- Vérifiez que `FIREBASE_API_KEY` est correctement définie

### Erreur "auth/unauthorized-domain"
- Ajoutez votre domaine dans Firebase Console → Authentication → Settings → Authorized domains

### Erreur de popup bloquée
- Vérifiez que les popups sont autorisées dans le navigateur
- Utilisez la redirection comme alternative si nécessaire

### Erreur "auth/network-request-failed"
- Vérifiez votre connexion internet
- Vérifiez que les URLs Firebase sont accessibles
