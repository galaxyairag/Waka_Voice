# Waka Voice Burkina

Plateforme d'agents vocaux IA pour le Burkina Faso - Application Flask permettant de créer et gérer des agents conversationnels intelligents avec synthèse vocale personnalisée.

## 📋 Fonctionnalités

- **Configuration dynamique d'avatars** avec personnalités et styles de voix personnalisés
- **Intégration Azure OpenAI** pour des conversations contextuelles intelligentes
- **Voix personnalisées** via Azure Personal Voice API
- **Gestion de l'historique** des conversations avec Azure Cosmos DB
- **Tableaux de bord** de production et qualité pour le suivi des performances
- **API RESTful** pour l'intégration avec des applications tierces
- **Upload en arrière-plan** de contenus audio et vidéo
- **Analyse de sentiment** et métriques de qualité conversationnelle

## 🚀 Technologies

- Python 3.x
- Flask
- Azure OpenAI
- Azure Cosmos DB
- Azure Speech Services
- Azure Blob Storage

## 📦 Installation

### Prérequis

- Python 3.8+
- Compte Azure avec accès aux services :
  - Azure OpenAI
  - Azure Cosmos DB
  - Azure Speech Services
  - Azure Blob Storage

### Étapes d'installation

1. **Cloner le repository**
```bash
git clone https://github.com/galaxyairag/Waka_Voice.git
cd Waka_Voice
```

2. **Créer un environnement virtuel**
```bash
python -m venv .venv
```

3. **Activer l'environnement virtuel**

Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```

Linux/Mac:
```bash
source .venv/bin/activate
```

4. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

5. **Configurer les variables d'environnement**

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# Azure Cosmos DB
COSMOS_ENDPOINT=your_cosmos_endpoint
COSMOS_KEY=your_cosmos_key
COSMOS_DATABASE_NAME=your_database_name
COSMOS_CONTAINER_NAME=your_container_name

# Azure Speech Services
AZURE_SPEECH_KEY=your_speech_key
AZURE_SPEECH_REGION=your_region

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER_NAME=your_container_name

# Flask
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=development
```

## 🏃‍♂️ Lancement de l'application

### Mode développement

```bash
python app.py
```

L'application sera accessible sur `http://localhost:5000`

### Mode production

Pour le déploiement en production, utilisez Gunicorn :

```bash
gunicorn --bind 0.0.0.0:8000 app:app
```

## 📁 Structure du projet

```
Waka_Voice/
├── app.py                      # Point d'entrée principal
├── requirements.txt            # Dépendances Python
├── Blueprints/                 # Routes Flask modulaires
│   ├── avatar_routes.py        # Gestion des avatars
│   ├── personal_voice_routes.py # API Personal Voice
│   ├── conversation_history_routes.py
│   └── ...
├── configuration/              # Configuration de l'application
│   ├── cosmos_config.py        # Configuration Cosmos DB
│   ├── voice_live_config.py    # Configuration voix
│   └── ...
├── tools/                      # Outils et utilitaires
├── static/                     # Fichiers statiques (CSS, JS, images)
├── templates/                  # Templates HTML
└── Scripts_test/              # Scripts de test et maintenance
```

## 🔧 Configuration des avatars

Les avatars peuvent être configurés via l'API ou directement dans Cosmos DB. Chaque avatar possède :

- **character** : Description de la personnalité
- **avatar_style** : Style visuel de l'avatar
- **voice_style** : Paramètres de la voix (ton, vitesse, style)
- **prompts personnalisés** : Instructions spécifiques pour l'IA

Voir `DOCUMENTATION_TECHNIQUE_AVATAR.md` pour plus de détails.

## 📚 Documentation

- [Documentation technique Avatar](DOCUMENTATION_TECHNIQUE_AVATAR.md)
- [Documentation Personal Voice API](DOCUMENTATION_PERSONAL_VOICE_API.md)
- [Refactoring Avatar Config](REFACTORING_AVATAR_CONFIG.md)

## 🔒 Sécurité

- Ne commitez **JAMAIS** le fichier `.env`
- Utilisez des secrets Azure Key Vault en production
- Activez l'authentification pour les endpoints critiques
- Vérifiez régulièrement les dépendances avec `pip audit`

## 🧪 Tests

```bash
# Lancer les tests unitaires
python -m pytest

# Scripts de test spécifiques
python Scripts_test/test_avatar_images.py
python Scripts_test/test_azure_avatar_api.py
```

## 📊 Tableaux de bord

L'application inclut deux tableaux de bord :

- **Dashboard Production** : Métriques en temps réel, utilisation des ressources
- **Dashboard Qualité** : Analyse de sentiment, qualité des conversations

Accès via `/production-dashboard` et `/quality-dashboard`

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commitez vos changements (`git commit -m 'Ajout nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

## 📝 Licence

[À définir]

## 👥 Auteurs

Projet développé pour Waka Voice Burkina

## 🆘 Support

Pour toute question ou problème, ouvrez une issue sur GitHub.

---

**Note** : Ce projet utilise des services Azure qui peuvent engendrer des coûts. Vérifiez votre utilisation régulièrement.
