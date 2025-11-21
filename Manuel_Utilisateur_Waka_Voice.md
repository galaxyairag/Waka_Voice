# Manuel d'Utilisation - Waka AI Voice Live

**Version 1.0**
**Application de Création et Gestion d'Agents Vocaux Intelligents**

---

# Table des Matières

1. [Introduction](#1-introduction)
2. [Premiers Pas](#2-premiers-pas)
3. [Tableau de Bord Principal](#3-tableau-de-bord-principal)
4. [Création d'un Agent Vocal](#4-création-dun-agent-vocal)
5. [Configuration des Avatars](#5-configuration-des-avatars)
6. [Gestion des Voix Personnalisées](#6-gestion-des-voix-personnalisées)
7. [Les Outils (Tools)](#7-les-outils-tools)
8. [Historique des Conversations](#8-historique-des-conversations)
9. [Tableaux de Bord Analytiques](#9-tableaux-de-bord-analytiques)
10. [Guide de Dépannage](#10-guide-de-dépannage)
11. [Glossaire](#11-glossaire)
12. [Annexes](#12-annexes)

---

# 1. Introduction

## 1.1 Qu'est-ce que Waka AI Voice Live ?

Waka AI Voice Live est une plateforme complète de création et de gestion d'agents conversationnels vocaux. Elle permet de créer des assistants virtuels capables de :

- **Converser naturellement** avec les utilisateurs par la voix
- **Exécuter des actions** grâce à des outils intégrés (météo, emails, recherches, etc.)
- **S'adapter visuellement** avec des avatars animés
- **Utiliser des voix personnalisées** pour une expérience unique

## 1.2 À qui s'adresse ce manuel ?

Ce manuel est destiné aux utilisateurs souhaitant :
- Créer leur premier agent vocal
- Configurer des assistants pour leur entreprise
- Personnaliser l'expérience utilisateur avec des avatars
- Analyser les performances de leurs agents

## 1.3 Prérequis

Avant de commencer, assurez-vous de disposer de :
- Un navigateur web moderne (Chrome, Firefox, Edge, Safari)
- Une connexion internet stable
- Un microphone fonctionnel (pour tester les agents)
- Vos identifiants de connexion à la plateforme

## 1.4 Vue d'ensemble de l'application

L'application se compose de plusieurs modules principaux :

| Module | Description |
|--------|-------------|
| **Agents Vocaux** | Création et gestion d'agents conversationnels |
| **Avatars** | Configuration d'agents avec représentation visuelle |
| **Voix Personnalisées** | Création de voix uniques à partir d'enregistrements |
| **Historique** | Consultation des conversations passées |
| **Tableaux de Bord** | Analyse des performances et de la qualité |

---

# 2. Premiers Pas

## 2.1 Accéder à l'application

Pour accéder à Waka AI Voice Live :

1. Ouvrez votre navigateur web
2. Saisissez l'adresse de l'application fournie par votre administrateur
3. La page d'accueil s'affiche avec le tableau de bord principal

## 2.2 Comprendre l'interface

### 2.2.1 La barre de navigation

La barre de navigation en haut de l'écran donne accès à :

- **Accueil** : Retour au tableau de bord principal
- **Agents** : Liste de tous vos agents créés
- **Avatars** : Galerie des agents avec avatars
- **Créer une Voix** : Module de création de voix personnalisées
- **Qualité** : Tableau de bord qualité
- **Production** : Tableau de bord de production

### 2.2.2 Le tableau de bord

Le tableau de bord affiche :
- Les statistiques du jour (appels, durée moyenne, etc.)
- Les agents récemment créés ou modifiés
- Les alertes et notifications importantes

## 2.3 Navigation dans l'application

### Conseils de navigation :

1. **Fil d'Ariane** : Utilisez le fil d'Ariane en haut des pages pour revenir aux étapes précédentes
2. **Boutons d'action** : Les boutons bleus sont des actions principales, les gris sont secondaires
3. **Icônes** : Survolez les icônes pour voir des infobulles explicatives
4. **Formulaires** : Les champs marqués d'un astérisque (*) sont obligatoires

---

# 3. Tableau de Bord Principal

## 3.1 Vue d'ensemble

Le tableau de bord principal est votre point de départ quotidien. Il présente une synthèse de l'activité de vos agents vocaux.

## 3.2 Les indicateurs clés (KPI)

### 3.2.1 Indicateurs affichés

| Indicateur | Description |
|------------|-------------|
| **Appels du jour** | Nombre total de conversations initiées aujourd'hui |
| **Durée moyenne** | Durée moyenne des conversations en minutes |
| **Taux de résolution** | Pourcentage de conversations résolues avec succès |
| **Agents actifs** | Nombre d'agents actuellement déployés |

### 3.2.2 Lecture des graphiques

Les graphiques sparkline montrent l'évolution sur les 7 derniers jours :
- **Tendance verte** : Amélioration
- **Tendance rouge** : Détérioration
- **Tendance grise** : Stable

## 3.3 Actions rapides

Depuis le tableau de bord, vous pouvez :

1. **Créer un nouvel agent** : Cliquez sur "Nouvel Agent"
2. **Voir tous les agents** : Cliquez sur "Voir tout" dans la section Agents
3. **Accéder à l'historique** : Cliquez sur une conversation récente

---

# 4. Création d'un Agent Vocal

La création d'un agent vocal se fait en **5 étapes** guidées. Chaque étape vous permet de configurer un aspect spécifique de votre agent.

## 4.1 Étape 1 : Sélection du Modèle

### 4.1.1 Accéder à la création

1. Cliquez sur **"Agents"** dans la navigation
2. Cliquez sur le bouton **"Créer un Agent"**
3. Vous arrivez sur la page de sélection du modèle

### 4.1.2 Choisir un modèle

Plusieurs modèles sont disponibles selon vos besoins :

#### Modèles Realtime (Recommandé)

| Modèle | Caractéristiques | Cas d'usage |
|--------|------------------|-------------|
| **GPT-4o Realtime Preview** | Ultra-rapide, multimodal | Conversations naturelles, agents généraux |
| **GPT-4o Mini Realtime** | Rapide, économique | Agents simples, volume élevé |

#### Comment choisir ?

- **Pour des conversations complexes** : Choisissez GPT-4o Realtime Preview
- **Pour des agents simples et nombreux** : Choisissez GPT-4o Mini Realtime

### 4.1.3 Valider le choix

1. Cliquez sur la carte du modèle souhaité
2. Vérifiez les informations affichées
3. Cliquez sur **"Continuer"** pour passer à l'étape suivante

## 4.2 Étape 2 : Configuration Voice Live

Cette étape permet de configurer les paramètres audio et de détection vocale de votre agent.

### 4.2.1 Configuration Audio

#### Format d'entrée audio

| Paramètre | Valeur recommandée | Description |
|-----------|-------------------|-------------|
| **Taux d'échantillonnage** | 24000 Hz | Qualité standard pour la voix |
| **Annulation d'écho** | Activé | Réduit les échos lors des appels |
| **Réduction de bruit** | Activé | Améliore la clarté dans les environnements bruyants |

#### Comment configurer :

1. **Annulation d'écho** : Cochez la case si vos utilisateurs appellent depuis des environnements avec haut-parleurs
2. **Réduction de bruit** : Cochez la case pour les environnements bruyants (open space, extérieur)

### 4.2.2 Détection de la Parole (VAD)

Le VAD (Voice Activity Detection) détermine quand l'utilisateur parle et quand il a fini.

#### Paramètres principaux

| Paramètre | Plage | Description |
|-----------|-------|-------------|
| **Seuil de détection** | 0.0 - 1.0 | Sensibilité de détection (0.5 recommandé) |
| **Padding préfixe** | 100 - 500 ms | Temps avant le début de la parole capturé |
| **Durée de parole** | 50 - 200 ms | Durée minimale pour considérer qu'il y a parole |
| **Durée de silence** | 300 - 1000 ms | Silence nécessaire pour considérer la fin de parole |

#### Conseils de configuration :

- **Seuil bas (0.3)** : Pour les voix faibles ou environnements calmes
- **Seuil haut (0.7)** : Pour les environnements bruyants
- **Silence court (300 ms)** : Conversations rapides
- **Silence long (800 ms)** : Conversations réfléchies (support technique)

### 4.2.3 Configuration de la Voix

Choisissez la voix de votre agent parmi les voix Azure disponibles.

#### Types de voix

1. **Voix Standard Azure** : Voix professionnelles multilingues
2. **Voix Personnalisée** : Voix créées à partir de vos enregistrements (voir section 6)

#### Sélection de la voix :

1. Cliquez sur le sélecteur de voix
2. Utilisez les filtres pour trouver une voix :
   - **Langue** : Français, Anglais, etc.
   - **Genre** : Masculin, Féminin
   - **Style** : Professionnel, Amical, etc.
3. Cliquez sur l'icône de lecture pour prévisualiser
4. Sélectionnez la voix souhaitée

#### Paramètres de la voix

| Paramètre | Description |
|-----------|-------------|
| **Vitesse** | Rapidité d'élocution (0.5 à 2.0, normal = 1.0) |
| **Tonalité** | Hauteur de la voix |
| **Volume** | Niveau sonore de la voix |

### 4.2.4 Transcription

Activez la transcription pour obtenir le texte des conversations.

1. Cochez **"Activer la transcription"**
2. Sélectionnez la langue principale de transcription
3. Optionnel : Ajoutez des mots spécifiques au vocabulaire (noms propres, termes techniques)

### 4.2.5 Valider l'étape 2

1. Vérifiez tous les paramètres configurés
2. Cliquez sur **"Continuer"** pour passer à l'étape 3

## 4.3 Étape 3 : Sélection des Outils

Les outils permettent à votre agent d'effectuer des actions concrètes pendant la conversation.

### 4.3.1 Comprendre les outils

Un outil (ou "tool") est une fonction que l'agent peut appeler pour :
- Rechercher des informations
- Envoyer des messages
- Effectuer des calculs
- Et bien plus...

### 4.3.2 Liste des outils disponibles

#### Outils d'Information

| Outil | Fonction | Exemple d'utilisation |
|-------|----------|----------------------|
| **Météo** | Prévisions météorologiques | "Quel temps fait-il à Paris ?" |
| **Actualités** | Dernières nouvelles | "Quelles sont les actualités du jour ?" |
| **Recherche Web** | Recherche sur internet | "Cherche des informations sur..." |
| **Lieux** | Recherche de lieux | "Trouve un restaurant près de moi" |

#### Outils de Communication

| Outil | Fonction | Exemple d'utilisation |
|-------|----------|----------------------|
| **Email** | Envoi d'emails | "Envoie un email à mon contact" |
| **Traducteur** | Traduction de texte | "Traduis 'bonjour' en anglais" |

#### Outils de Voyage

| Outil | Fonction | Exemple d'utilisation |
|-------|----------|----------------------|
| **Recherche de vols** | Trouver des vols | "Trouve un vol Paris-New York" |
| **Réservation de vol** | Réserver un vol | "Réserve ce vol" |
| **Recherche d'hôtels** | Trouver des hôtels | "Trouve un hôtel à Lyon" |
| **Réservation d'hôtel** | Réserver un hôtel | "Réserve cet hôtel" |
| **Estimation taxi** | Estimer le prix d'une course | "Combien coûte un taxi jusqu'à l'aéroport ?" |
| **Horaires de bus** | Consulter les horaires | "À quelle heure passe le prochain bus ?" |

#### Outils Utilitaires

| Outil | Fonction | Exemple d'utilisation |
|-------|----------|----------------------|
| **Calculatrice** | Calculs mathématiques | "Combien font 15% de 250 ?" |
| **Convertisseur de devises** | Conversion monétaire | "Convertis 100 euros en dollars" |
| **Horaires de prière** | Heures de prière | "À quelle heure est la prière du soir ?" |
| **Calculateur d'impôts** | Estimation fiscale | "Estime mes impôts" |

#### Outils Spécialisés

| Outil | Fonction | Exemple d'utilisation |
|-------|----------|----------------------|
| **Conseils santé** | Informations médicales générales | "J'ai mal à la tête, que faire ?" |
| **Exercices** | Programmes sportifs | "Propose-moi des exercices pour le dos" |
| **Pharmacies** | Trouver une pharmacie | "Où est la pharmacie la plus proche ?" |
| **Services gouvernementaux** | Informations administratives | "Comment renouveler ma carte d'identité ?" |
| **Informations scolaires** | Renseignements sur les écoles | "Quelles sont les écoles du quartier ?" |
| **Base de connaissances** | Recherche dans vos documents | "Cherche dans nos procédures" |
| **Création de CV** | Générer un CV | "Aide-moi à créer mon CV" |

#### Outil de Fin de Conversation

| Outil | Fonction |
|-------|----------|
| **Fin de conversation** | Termine proprement l'appel |

### 4.3.3 Comment sélectionner les outils

1. Parcourez la liste des outils disponibles
2. Cochez les outils pertinents pour votre agent
3. Les outils sélectionnés apparaissent avec une coche verte

#### Bonnes pratiques :

- **Sélectionnez uniquement les outils nécessaires** : Trop d'outils peuvent ralentir l'agent
- **Pensez aux cas d'usage** : Quelles actions vos utilisateurs demanderont-ils ?
- **Toujours inclure "Fin de conversation"** : Permet de terminer proprement les appels

### 4.3.4 Valider l'étape 3

1. Vérifiez les outils sélectionnés
2. Cliquez sur **"Continuer"** pour passer à l'étape 4

## 4.4 Étape 4 : Instructions et Persona

Cette étape est cruciale : vous définissez la personnalité et le comportement de votre agent.

### 4.4.1 Nom du projet

Donnez un nom identifiable à votre agent :
- **Exemple** : "Assistant Support Client", "Agent Réservation", "Conseiller RH"

### 4.4.2 Le Prompt Système

Le prompt système est un texte qui définit le comportement de l'agent. C'est son "mode d'emploi".

#### Structure recommandée :

```
## RÔLE
Tu es [rôle de l'agent], travaillant pour [entreprise].

## TON
Tu adoptes un ton [familier/professionnel/chaleureux].

## MISSIONS PRINCIPALES
1. [Mission 1]
2. [Mission 2]
3. [Mission 3]

## COMPORTEMENT
- Salue l'utilisateur au premier message uniquement
- Demande le prénom pour personnaliser l'échange
- Utilise les outils disponibles pour répondre aux demandes

## CONSIGNES SPÉCIFIQUES
[Ajoutez ici des instructions particulières]
```

### 4.4.3 Générateur de prompt

L'application propose un générateur automatique de prompt :

1. Cliquez sur **"Générer un prompt"**
2. Décrivez votre agent en quelques phrases :
   - Son rôle
   - Son contexte d'utilisation
   - Les particularités souhaitées
3. Cliquez sur **"Générer"**
4. Le prompt est créé automatiquement
5. Modifiez-le si nécessaire

#### Exemple de description pour le générateur :

> "Un assistant pour une agence de voyage qui aide les clients à réserver des vols et hôtels. Il doit être amical et professionnel, parler français avec quelques expressions locales."

### 4.4.4 Conseils pour un bon prompt

#### À faire :
- Être précis sur le rôle
- Définir le ton de communication
- Lister les actions autorisées
- Préciser les limites (ce que l'agent ne doit pas faire)

#### À éviter :
- Instructions contradictoires
- Prompts trop longs (risque de confusion)
- Langage ambigu

### 4.4.5 Champs complémentaires

| Champ | Description |
|-------|-------------|
| **Prénom de l'assistant** | Le nom par lequel l'agent se présente |
| **Rôle** | Fonction de l'agent (assistant, conseiller, etc.) |
| **Ton** | Style de communication souhaité |
| **Terminologie** | Vocabulaire spécifique à utiliser |
| **Consignes de conduite** | Règles comportementales supplémentaires |

### 4.4.6 Valider l'étape 4

1. Relisez attentivement le prompt système
2. Vérifiez que toutes les instructions sont claires
3. Cliquez sur **"Terminer la configuration"**

## 4.5 Test de l'Agent

Après la configuration, vous pouvez tester votre agent immédiatement.

### 4.5.1 Interface de test

L'écran de test simule un appel téléphonique :
- Un téléphone virtuel affiche la conversation
- Le microphone de votre ordinateur capture votre voix
- L'agent répond en temps réel

### 4.5.2 Lancer un test

1. Cliquez sur le bouton **"Appeler"** (icône téléphone vert)
2. Autorisez l'accès au microphone si demandé
3. Attendez la connexion (quelques secondes)
4. L'agent vous salue et la conversation commence

### 4.5.3 Pendant le test

- **Parlez naturellement** comme lors d'un vrai appel
- **Testez différents scénarios** : questions simples, demandes complexes
- **Observez les réponses** : sont-elles pertinentes ? Le ton est-il correct ?

### 4.5.4 Terminer le test

1. Dites "Au revoir" ou une formule de fin
2. Ou cliquez sur le bouton **"Raccrocher"** (icône téléphone rouge)
3. La conversation se termine et est enregistrée dans l'historique

### 4.5.5 Analyser les résultats

Après le test, vous pouvez :
- Consulter la transcription complète
- Voir les outils utilisés par l'agent
- Identifier les points d'amélioration

---

# 5. Configuration des Avatars

Les avatars ajoutent une dimension visuelle à vos agents vocaux. Un avatar est une représentation animée qui accompagne la voix.

## 5.1 Qu'est-ce qu'un Avatar ?

Un avatar est un personnage virtuel qui :
- **Synchronise ses lèvres** avec la parole
- **Montre des expressions** adaptées au contexte
- **Crée une connexion visuelle** avec l'utilisateur

## 5.2 Accéder à la galerie des Avatars

1. Cliquez sur **"Avatars"** dans la navigation
2. La galerie affiche tous vos agents avec avatars
3. Vous voyez des statistiques : nombre total, actifs, en configuration

## 5.3 Créer un Agent avec Avatar

### 5.3.1 Étape 1 : Sélection du Modèle

Identique à la création d'un agent vocal standard :
1. Cliquez sur **"Créer un Avatar"**
2. Choisissez le modèle de langage
3. Cliquez sur **"Continuer"**

### 5.3.2 Étape 2 : Configuration Voix et Avatar

Cette étape combine la configuration vocale et la sélection de l'avatar.

#### Sélection de la voix

Choisissez une voix compatible avec les avatars :
- Voix Azure standard
- Voix personnalisée (si vous en avez créé)

#### Sélection du personnage avatar

Les avatars disponibles sont présentés sous forme de cartes :

| Avatar | Description | Styles disponibles |
|--------|-------------|-------------------|
| **Lisa** | Avatar féminin professionnel | Casual, Graceful, Technical |
| **Harry** | Avatar masculin business | Business, Casual, Youthful |
| **Jeff** | Avatar masculin formel | Business, Formal |
| **Lori** | Avatar féminin élégant | Casual, Graceful, Formal |
| **Max** | Avatar masculin moderne | Business, Casual, Formal |
| **Meg** | Avatar féminin dynamique | Formal, Casual, Business |

#### Comment choisir un avatar :

1. Parcourez les avatars disponibles
2. Cliquez sur un avatar pour le sélectionner
3. Choisissez un **style** parmi ceux proposés :
   - **Casual** : Décontracté, adapté aux échanges informels
   - **Business** : Professionnel, pour un contexte corporate
   - **Technical** : Sobre, pour du support technique
   - **Graceful** : Élégant, pour l'accueil ou le premium

#### Configuration de l'arrière-plan

| Option | Description |
|--------|-------------|
| **Couleur unie** | Choisissez une couleur avec le sélecteur |
| **Image personnalisée** | Uploadez une image de fond |

### 5.3.3 Étape 3 : Sélection des Outils

Identique à la création d'un agent vocal (voir section 4.3).

### 5.3.4 Étape 4 : Instructions et Prompt

Identique à la création d'un agent vocal (voir section 4.4).

## 5.4 Tester un Agent Avatar

### 5.4.1 Lancer le test

1. Depuis la galerie, cliquez sur un avatar
2. Cliquez sur **"Appeler"**
3. L'avatar apparaît à l'écran et commence à parler

### 5.4.2 Observer l'avatar

Pendant la conversation :
- L'avatar bouge les lèvres de façon synchronisée
- Les expressions s'adaptent au contenu
- L'arrière-plan configuré est visible

## 5.5 Gérer les Avatars

### 5.5.1 Modifier un avatar

1. Dans la galerie, cliquez sur l'icône **"Modifier"** de l'avatar
2. Modifiez les paramètres souhaités
3. Sauvegardez les modifications

### 5.5.2 Supprimer un avatar

1. Cliquez sur l'icône **"Supprimer"**
2. Confirmez la suppression
3. L'avatar est définitivement supprimé

---

# 6. Gestion des Voix Personnalisées

Les voix personnalisées vous permettent de créer une voix unique à partir d'enregistrements.

## 6.1 Pourquoi créer une voix personnalisée ?

- **Identité de marque** : Une voix unique reconnaissable
- **Personnalisation** : Reproduire la voix d'un porte-parole
- **Différenciation** : Se démarquer des voix standard

## 6.2 Accéder au module

1. Cliquez sur **"Créer une Voix"** dans la navigation
2. Vous accédez à l'interface de création de voix personnalisée

## 6.3 Le processus de création

La création d'une voix personnalisée se fait en plusieurs étapes :

### 6.3.1 Étape 1 : Création du Projet

1. Cliquez sur **"Nouveau Projet"**
2. Remplissez les informations :
   - **Nom du projet** : Identifiant de la voix
   - **Description** : Contexte d'utilisation
3. Cliquez sur **"Créer"**

### 6.3.2 Étape 2 : Enregistrement du Consentement

Pour des raisons légales et éthiques, un consentement vocal est obligatoire.

#### Qu'est-ce que le consentement ?

Le locuteur (personne dont on enregistre la voix) doit :
- Donner son accord verbal
- Lire un texte de consentement spécifique
- Être informé de l'utilisation de sa voix

#### Procédure :

1. **Préparez le locuteur** : Expliquez le processus
2. **Affichez le texte de consentement** : Il apparaît à l'écran
3. **Lancez l'enregistrement** : Cliquez sur le bouton rouge
4. **Le locuteur lit le texte** : Clairement et naturellement
5. **Arrêtez l'enregistrement** : Cliquez sur stop
6. **Validez la transcription** : Vérifiez que le texte correspond

#### Texte de consentement type :

> "Je, [prénom et nom], suis conscient(e) que les enregistrements de ma voix seront utilisés par [nom de l'entreprise] pour créer et utiliser une version synthétique de ma voix."

### 6.3.3 Étape 3 : Enregistrement des échantillons vocaux

Pour créer une voix de qualité, plusieurs enregistrements sont nécessaires.

#### Conseils pour de bons enregistrements :

| Aspect | Recommandation |
|--------|----------------|
| **Environnement** | Pièce calme, sans écho |
| **Microphone** | Qualité correcte, à 15-20 cm de la bouche |
| **Élocution** | Naturelle, ni trop rapide ni trop lente |
| **Durée** | 5-10 minutes d'enregistrement au total |
| **Variété** | Phrases de différentes longueurs et intonations |

#### Procédure :

1. Cliquez sur **"Ajouter un enregistrement"**
2. Le texte à lire s'affiche
3. Cliquez sur **"Enregistrer"**
4. Lisez le texte naturellement
5. Cliquez sur **"Arrêter"**
6. Écoutez l'enregistrement pour vérifier la qualité
7. Validez ou recommencez si nécessaire
8. Répétez pour tous les textes proposés

### 6.3.4 Étape 4 : Création de la voix

Une fois tous les enregistrements validés :

1. Cliquez sur **"Créer la voix"**
2. Le système traite les enregistrements (peut prendre plusieurs minutes)
3. Une barre de progression indique l'avancement
4. À la fin, la voix est prête à être utilisée

## 6.4 Utiliser une voix personnalisée

### 6.4.1 Dans un agent vocal

1. Lors de la création d'un agent (Étape 2)
2. Dans le sélecteur de voix, choisissez **"Voix personnalisées"**
3. Sélectionnez votre voix dans la liste
4. Continuez la configuration normalement

### 6.4.2 Dans un agent avatar

Même procédure que pour un agent vocal.

## 6.5 Gérer vos voix personnalisées

### 6.5.1 Voir les voix créées

Dans le module "Créer une Voix", une liste affiche toutes vos voix :
- Nom de la voix
- Date de création
- Statut (Active, En cours, Erreur)

### 6.5.2 Tester une voix

1. Cliquez sur l'icône **"Test"** à côté de la voix
2. Saisissez un texte à faire lire
3. Cliquez sur **"Écouter"**
4. La voix synthétise le texte

### 6.5.3 Supprimer une voix

1. Cliquez sur l'icône **"Supprimer"**
2. Confirmez la suppression
3. La voix et tous ses enregistrements sont supprimés

---

# 7. Les Outils (Tools)

Cette section détaille chaque outil disponible pour vos agents.

## 7.1 Outils d'Information

### 7.1.1 Météo (get_weather_forecast)

**Description** : Fournit les prévisions météorologiques pour une ville donnée.

**Utilisation type** :
- "Quel temps fait-il à Paris ?"
- "Quelles sont les prévisions pour demain à Lyon ?"

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| city | Nom de la ville |
| days | Nombre de jours de prévision (1-7) |

### 7.1.2 Actualités (get_news)

**Description** : Récupère les dernières actualités.

**Utilisation type** :
- "Quelles sont les news du jour ?"
- "Des actualités sur la technologie ?"

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| category | Catégorie (general, tech, sports, etc.) |
| country | Code pays (fr, us, etc.) |

### 7.1.3 Recherche Web (search_web)

**Description** : Effectue une recherche sur internet.

**Utilisation type** :
- "Cherche des informations sur les énergies renouvelables"
- "Trouve la définition de blockchain"

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| query | Termes de recherche |

### 7.1.4 Lieux (search_places)

**Description** : Recherche des lieux à proximité.

**Utilisation type** :
- "Trouve un restaurant italien près de moi"
- "Où est la pharmacie la plus proche ?"

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| type | Type de lieu (restaurant, pharmacy, etc.) |
| location | Adresse ou coordonnées |

## 7.2 Outils de Communication

### 7.2.1 Email (send_email)

**Description** : Envoie un email.

**Utilisation type** :
- "Envoie un email à mon collègue"
- "Rédige et envoie un message à support@example.com"

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| to | Adresse email du destinataire |
| subject | Objet de l'email |
| body | Contenu du message |

**Note** : L'agent collecte les informations une par une pour s'assurer de l'exactitude.

### 7.2.2 Traducteur (translate_text)

**Description** : Traduit du texte d'une langue à une autre.

**Utilisation type** :
- "Traduis 'bonjour' en anglais"
- "Comment dit-on 'merci' en espagnol ?"

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| text | Texte à traduire |
| source_lang | Langue source (optionnel, détection auto) |
| target_lang | Langue cible |

## 7.3 Outils de Voyage

### 7.3.1 Recherche de vols (search_flights)

**Description** : Recherche des vols disponibles.

**Utilisation type** :
- "Trouve un vol Paris-New York pour le 15 décembre"
- "Quels sont les vols pour Madrid demain ?"

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| origin | Ville ou code aéroport de départ |
| destination | Ville ou code aéroport d'arrivée |
| date | Date du vol |
| passengers | Nombre de passagers |

### 7.3.2 Réservation de vol (book_flight)

**Description** : Réserve un vol sélectionné.

**Utilisation type** :
- "Réserve ce vol"
- "Je veux prendre le vol de 10h"

### 7.3.3 Recherche d'hôtels (search_hotels)

**Description** : Recherche des hôtels disponibles.

**Utilisation type** :
- "Trouve un hôtel à Lyon pour le week-end"
- "Quels hôtels sont disponibles près de la Tour Eiffel ?"

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| location | Ville ou adresse |
| check_in | Date d'arrivée |
| check_out | Date de départ |
| guests | Nombre de personnes |

### 7.3.4 Réservation d'hôtel (book_hotel)

**Description** : Réserve un hôtel sélectionné.

### 7.3.5 Estimation taxi (estimate_taxi_fare)

**Description** : Estime le coût d'une course en taxi.

**Utilisation type** :
- "Combien coûte un taxi jusqu'à l'aéroport ?"
- "Estimation du prix pour aller en centre-ville"

### 7.3.6 Horaires de bus (get_bus_schedule)

**Description** : Consulte les horaires de bus.

**Utilisation type** :
- "À quelle heure passe le prochain bus ?"
- "Horaires de la ligne 42"

## 7.4 Outils Utilitaires

### 7.4.1 Calculatrice (calculate)

**Description** : Effectue des calculs mathématiques.

**Utilisation type** :
- "Combien font 15% de 250 ?"
- "Calcule 1250 divisé par 8"
- "Quel est le résultat de 45 fois 32 ?"

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| expression | Expression mathématique à calculer |

### 7.4.2 Convertisseur de devises (convert_currency)

**Description** : Convertit des montants entre devises.

**Utilisation type** :
- "Convertis 100 euros en dollars"
- "Combien font 500 livres en euros ?"

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| amount | Montant à convertir |
| from_currency | Devise source |
| to_currency | Devise cible |

### 7.4.3 Horaires de prière (get_prayer_times)

**Description** : Donne les horaires de prière pour une localité.

**Utilisation type** :
- "À quelle heure est la prière du soir ?"
- "Horaires de prière à Casablanca"

### 7.4.4 Calculateur d'impôts (calculate_tax)

**Description** : Estime les impôts selon les paramètres fournis.

**Utilisation type** :
- "Estime mes impôts pour un revenu de 40000 euros"
- "Quel serait mon impôt avec ces revenus ?"

## 7.5 Outils Spécialisés

### 7.5.1 Conseils santé (get_health_advice)

**Description** : Fournit des conseils de santé généraux (non médicaux).

**Utilisation type** :
- "J'ai mal à la tête, que faire ?"
- "Des conseils pour mieux dormir ?"

**Note** : L'agent précise toujours de consulter un professionnel de santé pour un avis médical.

### 7.5.2 Exercices (search_exercises)

**Description** : Propose des exercices physiques.

**Utilisation type** :
- "Propose-moi des exercices pour le dos"
- "Exercices de stretching pour le matin"

### 7.5.3 Pharmacies (find_pharmacy)

**Description** : Trouve les pharmacies à proximité, y compris celles de garde.

**Utilisation type** :
- "Où est la pharmacie la plus proche ?"
- "Quelle pharmacie est de garde ce soir ?"

### 7.5.4 Services gouvernementaux (get_government_service_info)

**Description** : Fournit des informations sur les démarches administratives.

**Utilisation type** :
- "Comment renouveler ma carte d'identité ?"
- "Quels documents pour un passeport ?"

### 7.5.5 Informations scolaires (get_school_info)

**Description** : Renseigne sur les établissements scolaires.

**Utilisation type** :
- "Quelles sont les écoles du quartier ?"
- "Dates des vacances scolaires"

### 7.5.6 Base de connaissances (search_knowledge_base)

**Description** : Recherche dans une base documentaire personnalisée.

**Utilisation type** :
- "Cherche dans nos procédures internes"
- "Quelle est la politique de remboursement ?"

### 7.5.7 Création de CV (create_cv)

**Description** : Aide à créer un curriculum vitae.

**Utilisation type** :
- "Aide-moi à créer mon CV"
- "Je veux mettre à jour mon CV"

**Note** : L'agent collecte les informations progressivement.

## 7.6 Outil Système

### 7.6.1 Fin de conversation (end_conversation)

**Description** : Termine proprement la conversation.

**Utilisation type** :
- Appelé automatiquement quand l'utilisateur dit "au revoir"
- Peut être déclenché par l'agent après avoir accompli sa tâche

**Paramètres** :
| Paramètre | Description |
|-----------|-------------|
| reason | Raison de la fin (salutation, tâche_complétée, etc.) |

---

# 8. Historique des Conversations

L'historique vous permet de consulter toutes les conversations passées de vos agents.

## 8.1 Accéder à l'historique

1. Cliquez sur **"Historique"** dans la navigation
2. La liste des conversations s'affiche

## 8.2 Comprendre la liste

Chaque conversation affiche :
| Information | Description |
|-------------|-------------|
| **Date/Heure** | Moment de la conversation |
| **Agent** | Nom de l'agent utilisé |
| **Durée** | Durée totale de l'appel |
| **Statut** | Terminé, En cours, Échoué |
| **Sentiment** | Analyse du ton de la conversation |

## 8.3 Filtrer les conversations

Utilisez les filtres pour trouver une conversation :

- **Par date** : Sélectionnez une plage de dates
- **Par agent** : Choisissez un agent spécifique
- **Par statut** : Filtrez par état de la conversation
- **Par sentiment** : Positif, Neutre, Négatif

## 8.4 Consulter une conversation

1. Cliquez sur une ligne de l'historique
2. Le détail s'affiche :

### 8.4.1 Transcription

La transcription complète montre :
- **Messages utilisateur** : Ce que l'utilisateur a dit
- **Réponses agent** : Ce que l'agent a répondu
- **Appels d'outils** : Les outils utilisés et leurs résultats

### 8.4.2 Métriques

| Métrique | Description |
|----------|-------------|
| **Durée totale** | Temps de la conversation |
| **Nombre d'échanges** | Nombre de tours de parole |
| **Outils utilisés** | Liste des outils appelés |
| **Tokens consommés** | Ressources utilisées |

### 8.4.3 Analyse de sentiment

L'analyse de sentiment évalue le ton de la conversation :
- **Sentiment utilisateur** : Comment s'est senti l'utilisateur
- **Sentiment agent** : Ton adopté par l'agent

## 8.5 Exporter l'historique

Pour exporter les données :

1. Sélectionnez les conversations souhaitées
2. Cliquez sur **"Exporter"**
3. Choisissez le format (CSV, JSON)
4. Téléchargez le fichier

---

# 9. Tableaux de Bord Analytiques

Les tableaux de bord vous permettent d'analyser les performances de vos agents.

## 9.1 Tableau de Bord Qualité

### 9.1.1 Accès

Cliquez sur **"Qualité"** dans la navigation.

### 9.1.2 Indicateurs affichés

| Indicateur | Description |
|------------|-------------|
| **Taux de résolution** | % de conversations résolues avec succès |
| **Satisfaction estimée** | Score de satisfaction basé sur l'analyse de sentiment |
| **Temps de réponse moyen** | Délai moyen de réponse de l'agent |
| **Taux d'escalade** | % de conversations nécessitant une intervention humaine |

### 9.1.3 Graphiques

- **Évolution dans le temps** : Tendances sur la période sélectionnée
- **Répartition par agent** : Comparaison entre agents
- **Distribution des sentiments** : Positif, Neutre, Négatif

### 9.1.4 Filtres disponibles

- **Période** : Jour, Semaine, Mois, Personnalisé
- **Agent** : Tous ou agent spécifique
- **Statut** : Toutes conversations ou filtrées

## 9.2 Tableau de Bord Production

### 9.2.1 Accès

Cliquez sur **"Production"** dans la navigation.

### 9.2.2 Indicateurs affichés

| Indicateur | Description |
|------------|-------------|
| **Volume d'appels** | Nombre total de conversations |
| **Durée totale** | Temps cumulé de conversation |
| **Pic d'activité** | Heures de forte affluence |
| **Coût estimé** | Consommation en ressources |

### 9.2.3 Graphiques

- **Volume par heure** : Distribution horaire des appels
- **Volume par jour** : Évolution quotidienne
- **Utilisation des outils** : Fréquence d'utilisation de chaque outil

### 9.2.4 Rapports

Générez des rapports détaillés :

1. Cliquez sur **"Générer un rapport"**
2. Sélectionnez la période
3. Choisissez les métriques à inclure
4. Cliquez sur **"Générer"**
5. Téléchargez le rapport en PDF

---

# 10. Guide de Dépannage

## 10.1 Problèmes de connexion

### Le microphone ne fonctionne pas

**Symptôme** : L'agent ne vous entend pas

**Solutions** :
1. Vérifiez que le microphone est bien connecté
2. Autorisez l'accès au microphone dans votre navigateur :
   - Chrome : Cliquez sur le cadenas dans la barre d'adresse > Microphone > Autoriser
   - Firefox : Menu > Préférences > Vie privée et sécurité > Permissions
3. Vérifiez le volume d'entrée de votre microphone dans les paramètres système
4. Essayez un autre navigateur

### L'agent ne répond pas

**Symptôme** : Silence après votre question

**Solutions** :
1. Vérifiez votre connexion internet
2. Rafraîchissez la page (F5)
3. Vérifiez que le statut de l'agent est "Actif"
4. Consultez les logs de l'application

## 10.2 Problèmes de qualité audio

### La voix de l'agent est saccadée

**Symptôme** : Coupures dans la voix de l'agent

**Solutions** :
1. Vérifiez votre bande passante internet
2. Fermez les applications consommant du réseau
3. Essayez une connexion filaire plutôt que WiFi

### Écho pendant la conversation

**Symptôme** : Vous entendez votre propre voix en retour

**Solutions** :
1. Utilisez un casque plutôt que des haut-parleurs
2. Activez l'annulation d'écho dans la configuration de l'agent
3. Baissez le volume des haut-parleurs

## 10.3 Problèmes de comportement de l'agent

### L'agent ne comprend pas les questions

**Symptôme** : Réponses hors sujet

**Solutions** :
1. Vérifiez le prompt système : est-il clair et précis ?
2. Parlez clairement et évitez le bruit de fond
3. Reformulez vos questions de manière plus simple
4. Vérifiez la langue configurée

### L'agent n'utilise pas les outils

**Symptôme** : L'agent répond sans utiliser les outils disponibles

**Solutions** :
1. Vérifiez que les outils sont bien sélectionnés (Étape 3)
2. Ajoutez des instructions explicites dans le prompt système
3. Testez avec des demandes directes ("Quelle est la météo à Paris ?")

### L'agent utilise mal les outils

**Symptôme** : Résultats incorrects ou erreurs

**Solutions** :
1. Vérifiez les paramètres transmis aux outils
2. Simplifiez les demandes
3. Consultez l'historique pour identifier les erreurs

## 10.4 Problèmes avec les avatars

### L'avatar ne s'affiche pas

**Symptôme** : Écran noir ou absent

**Solutions** :
1. Vérifiez que votre navigateur supporte WebRTC
2. Mettez à jour votre navigateur
3. Désactivez les bloqueurs de contenu
4. Essayez un autre navigateur (Chrome recommandé)

### La synchronisation labiale est décalée

**Symptôme** : Les lèvres bougent en retard ou avance

**Solutions** :
1. Rafraîchissez la page
2. Vérifiez votre connexion internet
3. Réduisez la qualité vidéo si disponible

## 10.5 Problèmes de voix personnalisée

### La création de voix échoue

**Symptôme** : Message d'erreur lors de la création

**Solutions** :
1. Vérifiez la qualité des enregistrements :
   - Pas de bruit de fond
   - Volume suffisant
   - Énonciation claire
2. Respectez le format audio requis (WAV, 16 kHz minimum)
3. Assurez-vous d'avoir enregistré suffisamment d'échantillons
4. Réenregistrez les échantillons de mauvaise qualité

### La voix personnalisée sonne artificielle

**Symptôme** : Résultat peu naturel

**Solutions** :
1. Augmentez le nombre d'échantillons vocaux
2. Variez les intonations dans les enregistrements
3. Utilisez un meilleur microphone
4. Enregistrez dans un environnement acoustiquement traité

---

# 11. Glossaire

| Terme | Définition |
|-------|------------|
| **Agent** | Programme conversationnel capable de dialoguer avec un utilisateur |
| **Avatar** | Représentation visuelle animée d'un agent |
| **Consentement** | Accord verbal enregistré pour la création d'une voix personnalisée |
| **Modèle** | Intelligence artificielle sous-jacente (GPT-4, etc.) |
| **Outil (Tool)** | Fonction que l'agent peut appeler pour effectuer une action |
| **Prompt** | Instructions textuelles définissant le comportement de l'agent |
| **Token** | Unité de mesure du traitement de texte par l'IA |
| **Transcription** | Conversion de la parole en texte |
| **VAD** | Voice Activity Detection - Détection d'activité vocale |
| **Voice Live** | Technologie de conversation vocale en temps réel |
| **WebRTC** | Technologie de communication temps réel dans le navigateur |

---

# 12. Annexes

## Annexe A : Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| **Espace** | Démarrer/Arrêter l'enregistrement (lors des tests) |
| **Échap** | Fermer une fenêtre modale |
| **Entrée** | Valider un formulaire |

## Annexe B : Formats supportés

### Audio
- WAV (recommandé)
- MP3
- OGG

### Images (arrière-plans avatars)
- PNG
- JPEG
- WebP

## Annexe C : Limites techniques

| Élément | Limite |
|---------|--------|
| Durée maximale d'une conversation | 30 minutes |
| Taille maximale d'un enregistrement | 100 Mo |
| Nombre d'outils par agent | 20 maximum recommandé |
| Longueur du prompt système | 8000 caractères maximum |

## Annexe D : Bonnes pratiques

### Pour de meilleures conversations

1. **Définissez clairement le rôle** de l'agent dans le prompt
2. **Limitez le nombre d'outils** aux fonctions essentielles
3. **Testez régulièrement** avec différents scénarios
4. **Analysez l'historique** pour identifier les points d'amélioration
5. **Mettez à jour le prompt** en fonction des retours utilisateurs

### Pour de meilleurs enregistrements vocaux

1. **Environnement calme** : Pas de bruit de fond
2. **Microphone de qualité** : USB ou XLR recommandé
3. **Distance constante** : 15-20 cm du microphone
4. **Hydratation** : Boire de l'eau avant d'enregistrer
5. **Pauses** : Faire des pauses entre les sessions

## Annexe E : Support

Pour toute question ou problème :

1. Consultez d'abord ce manuel
2. Vérifiez le guide de dépannage (Section 10)
3. Contactez le support technique de votre organisation

---

**Fin du Manuel d'Utilisation**

*Document généré pour Waka AI Voice Live v1.0*
*Dernière mise à jour : Novembre 2025*
