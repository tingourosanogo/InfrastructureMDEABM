# 📑 Documentation Détaillée de moteur de transformation vers le code GAMA

```text
Requirement 
- pip install lxml
- pip install jinja2
- pip install lark
- pip install pytest pytest-cov   // pour les tests unitaires


- pip install rembg pillow // rembg utilise un modèle IA pour supprimer l’arrière-plan d'une image 
```



## Table des Matières

- [La Phase I : Analyse IDM (PIM & Sources Comportementales)](#la-phase-i--analyse-idm-pim--sources-comportementales)
- [La Phase II : Étude Comparative des Outils de Transformation M2C](#la-phase-ii--étude-comparative-des-outils-de-transformation-m2c)
- [La Phase III : Conception des Règles de Mapping](#la-phase-iii--conception-des-règles-de-mapping)
- [Plan de Travail (Pipeline)](#plan-de-travail-pipeline)
- [Implémentation](#la-phase-iv--implémentation)
- [Données](#données)

## La Phase I : Analyse IDM (PIM & Sources Comportementales)

Ce document compile les résultats de l'analyse du Métamodèle Ecore final (`pimSocioecosytemMM.ecore`), du modèle d'application (XMI) et des sources de données externes (JSON/YAML/CSV), confirmant la solidité de l'architecture pour la Génération Automatique de Code GAML.

### I. Analyse Détaillée du Métamodèle Ecore (PIM)

Le métamodèle sert de Langage Spécifique au Domaine (DSL) pour la description formelle des Socio-Écosystèmes (SES). Sa structure intègre désormais la sémantique nécessaire à la modélisation spatiale et comportementale.

#### 1. Structure Abstraite et Géométrique

La classe abstraite de base `NamedElement` est devenue le point de centralisation de l'identification et des données spatiales/graphiques, fondamentales pour toute simulation dans GAMA.

| Attribut           | Classe        | Type Ecore           | Rôle Sémantique                                      |
|--------------------|---------------|----------------------|-----------------------------------------------------|
| id                 | NamedElement  | EString (iD=true)    | Identifiant unique de l'entité (Clé Primaire).      |
| name               | NamedElement  | EString              | Nom lisible de l'entité.                           |
| description, comment| NamedElement  | EString              | Documentation de l'entité.                         |
| pos_x, pos_y       | NamedElement  | EDouble              | Coordonnées de l'entité dans l'espace de simulation. |
| width, height      | NamedElement  | EDouble              | Dimensions graphiques ou physiques de l'entité.    |



#### 2. Classes Principales et Relations de Composition

La classe `SocioEcosystem` agit comme le conteneur racine unique, assurant la cohésion du modèle :

- `SocioEcosystem` contient par composition (`containment=true`) les trois piliers du système : `agents`, `processes`, et `properties`.
- `Agent` conserve une relation d'agrégation réflexive (`containsAgents` / `partOfParentAgent`) pour modéliser les hiérarchies sans violer la règle d'unicité de la composition EMF.

#### 3. Sémantique Comportementale : Processus

La classe abstraite `Process` capture la logique d'exécution qui sera directement transformée en actions GAML :

| Attribut/Référence        | Classe  | Multiplicité | Rôle dans la Transformation GAML                        |
|---------------------------|---------|--------------|-------------------------------------------------------|
| equation                  | Process | 0..1         | Formule mathématique pure pour les calculs.           |
| pseudoCode                | Process | 0..1         | Logique algorithmique détaillée pour l'action GAML.   |
| subjects                  | Process | $$1..\*$$    | Agents qui initient l'action (`Agent.isSubjectOf`).   |
| objects                   | Process | $$0..\*$$    | Agents affectés par l'action (`Agent.isObjectOf`).    |
| dependsOnParameters       | Process | $$0..\*$$    | Facteurs d'influence non consommables.               |
| involvedResources         | Process | $$0..\*$$    | Ressources nécessaires à l'exécution du processus.    |



#### 4. Sémantique Comportementale : Ressources et Paramètres

La distinction des `Property` est cruciale pour la gestion des variables dans la simulation :

| Classe     | Attributs Spécifiques                     | Rôle dans GAMA                                              |
|------------|-------------------------------------------|------------------------------------------------------------|
| Resource   | quantity, isRenewable, heldBy (Agent).    | Variables d'état dynamiques (attributes) des espèces/agents. |
| Parameter  | value, isExogenous, parameterType.        | Variables globales ou constantes de la simulation (facteurs de configuration ou d'environnement). |



### II. Analyse des Sources de Données Externes (JSON/YAML/CSV)

Ces fichiers externes fournissent le contexte, l'initialisation et le comportement (*Quand* et *Pourquoi*) non inclus dans la structure pure du XMI. Le moteur de transformation GAML sera un moteur multi-sources.

#### 1. Contribution de chaque Template à la Transformation

| Fichier Template            | Section de Doc. Correspondante | Sémantique Fournie au Moteur GAML                                                                 |
|-----------------------------|--------------------------------|-----------------------------------------------------------------------------------------|
| introductionTemplate.json    | Introduction                   | Variables de Contrôle : Définit les objectifs globaux et les variables qui deviendront des entités de contrôle au niveau de l'objet `experiment` ou des variables globales. |
| indicatorTemplate.json      | Indicateurs                    | Sorties de Simulation : La `formula` et les `involvedAttributes` définissent les variables de sortie et les moniteurs GAML (bloc `output`). |
| initializationTemplate.json  | Initialisation                 | État Initial : Fournit les valeurs exactes des attributs et des paramètres pour le bloc `init` et la création des agents. Les `scenarios` serviront de base à la définition des différents blocs `experiment`. |
| userManuelTemplate.json     | Mode d'emploi                  | Expérimentation et Affichage : Dégage la structure des expérimentations (types d'affichage, `inputValues`, `outputValues`) et de la console GAML. |



#### 2. Gestion de la Sémantique de Déclenchement (*Le Quand*)

La sémantique de déclenchement d'un processus (*Le Quand*) sera inférée à partir des conventions appliquées aux champs textuels (comme `pseudoCode` ou `description`) ou intégrée aux fichiers JSON d'initialisation, permettant de définir les clauses `when` ou les conditions de l'action GAML sans alourdir le métamodèle Ecore.

### III. Validation de l'Architecture IDM et du Flux de Travail

L'analyse du `README.md` (Moteur de Documentation) confirme la faisabilité technique de la transformation M2C (Modèle vers Code).

| Point Validé                     | Implication pour le Moteur GAML                                                                 |
|----------------------------------|------------------------------------------------------------------------------------------------|
| Architecture Multi-Sources        | Le moteur doit ingérer simultanément : XMI (structure et logique) et JSON/YAML/CSV (contexte et initialisation). |
| Technologie de Base              | L'utilisation de Python et de bibliothèques XML/JSON (`lxml`, `json`) pour la transformation est la voie à suivre. |
| Parsers Existant                 | La logique de pré-traitement (YAML/CSV → JSON) est déjà implémentée et réutilisable, simplifiant l'ingestion des données comportementales. |
| Détermination de la Transformation| Le moteur passera d'une transformation M2D (Modèle vers Documentation) à une transformation M2C (Modèle vers Code) en utilisant le XMI comme source de vérité structurelle. |



---

## La Phase II : Étude Comparative des Outils de Transformation M2C

La transformation de modèles repose sur deux catégories d'outils principales : les frameworks dédiés à l'IDM (souvent basés sur Eclipse/Java) et les bibliothèques généralistes basées sur Python/XML.

### 1. Frameworks de Transformation Dédiés à l'IDM (Java/Eclipse)

Ces outils sont les standards de l'OMG (Object Management Group) pour l'IDM, offrant une puissance et une vérification formelle, mais nécessitant souvent un environnement Java/Eclipse.

| Outil/Technologie | Forces (M2C) | Faiblesses pour votre Contexte Python/lxml |
|-------------------|--------------|--------------------------------------------|
| **ATL (ATL Transformation Language)** | Le standard de facto pour la transformation de modèles (M2M/M2C). Offre une logique déclarative puissante (règles de matching et de forging). | Dépendance totale à Java/Eclipse. L'intégration dans votre pipeline Python/lxml nécessiterait d'exécuter l'outil via un appel système externe (processus lourd et peu élégant). |
| **Acceleo** | Spécialisé en M2C (Modèle vers Code). Utilise une approche impérative pour la génération de code basée sur des templates OCL. | Dépendance totale à Java/Eclipse. Moins flexible que Python pour lire des sources de données externes (JSON/YAML/CSV) dans le même processus de transformation. |
| **Xtend/Xtext** | Permet de créer des DSL personnalisés avec génération de code intégrée. | Surcharge et complexité inutiles, car notre DSL (Ecore) et notre éditeur graphique sont déjà finalisés. |



### 2. Solutions Basées sur Python (XML/Template)

Ces outils s'intègrent naturellement à votre pipeline Python existant et utilisent des technologies familières pour manipuler les fichiers XMI (qui sont des documents XML conformes au métamodèle Ecore).

| Outil/Technologie | Forces (M2C) | Faiblesses |
|-------------------|--------------|------------|
| **Jinja2 (avec Python)** | Template Engine le plus populaire de Python. Idéal pour la génération de la syntaxe GAML. Permet une séparation claire entre la logique d'extraction et le code cible. | Ne gère pas nativement la sémantique EMF/Ecore (relations, héritage). |
| **lxml (Python)** | Excellente performance XML. Idéal pour la lecture/navigation rapide et efficace des fichiers XMI (modèles sources). | Est un outil de bas niveau (XML), nécessitant beaucoup de code impératif Python pour implémenter la logique de transformation (parcours d'arbre XMI et traduction manuelle des relations EMF). |
| **XSLT (avec Python lxml)** | Approche déclarative pour la transformation XML → Texte (ou XML). Idéal pour les transformations directes et complexes d'arbres. | Moins intuitif que Jinja2 pour générer du code texte (GAML) avec une logique conditionnelle complexe. |
| **PyEcore / pYAMETL** | Des tentatives de frameworks IDM en Python. | Communauté plus petite et maturité inférieure aux standards Java/Eclipse. Risque de maintenance. |



### Synthèse et Recommandation Experte (Python-Native M2C)

Compte tenu de votre environnement Python existant, de l'utilisation confirmée de lxml pour le parsing XMI, et de la nécessité de lire des sources multiples (XMI + JSON/YAML), la recommandation est d'opter pour une approche hybride Python-Native :

#### Recommandation : Architecture lxml + Python Impératif + Jinja2

Cette solution est la plus efficace pour votre contexte :

- **Extraction du Modèle (M)** : Utiliser lxml (Python) pour lire les fichiers XMI (structure) et les fichiers JSON/YAML (comportement et initialisation). La logique Python impérative est utilisée pour extraire l'arbre XMI et créer un Modèle Intermédiaire (M') sous forme de structures de données Python (dictionnaires et objets).
- **Transformation et Génération de Code (C)** : Utiliser Jinja2 (Python) pour injecter le Modèle Intermédiaire (M') dans des templates GAML prédéfinis.
  - Les templates GAML définissent la structure fixe du code cible (species, init, action).
  - Le Modèle Intermédiaire (M') fournit les variables dynamiques (noms d'espèces, attributs, corps des actions/pseudoCode, valeurs d'initialisation JSON).

#### Avantages de l'Approche Recommandée

- **Intégration Parfaite** : S'intègre directement à votre pipeline Python existant sans dépendance externe à Java/Eclipse.
- **Contrôle Total** : Le code de transformation est écrit en Python, le langage de votre équipe.
- **Gestion Multi-Sources** : Python excelle dans la lecture simultanée et la fusion des données XMI, JSON, et YAML.
- **Lisibilité du Code GAML** : Jinja2 est spécifiquement conçu pour la génération de code lisible et maintenable.


## La phase III : Conception des règles de mapping 

**Règles de mapping (ou d'association) entre notre Métamodèle Ecore/XMI (le Modèle Source) et le Code GAML (le Modèle Cible).**

Ces règles formeront l'ossature de la logique Python dans votre moteur de transformation M2C.

### 🗺️ Conception des Règles de Mapping (Ecore → GAML)

La transformation est divisée en trois catégories : la structure des agents, les processus comportementaux et les données d'initialisation (qui nécessitent l'intégration des sources JSON/YAML).

#### I. Mapping des Classes Structurelles (Ecore Agent → GAML Species)

Les agents du Socio-Écosystème sont transformés en espèces (species) GAML. Les attributs et les ressources deviennent des variables d'état (attributs) de l'espèce.

| Concept Source (Ecore) | Élément Source (Attribut/Référence) | Concept Cible (GAML) | Règle de Transformation |
|------------------------|------------------------------------|----------------------|-----------------------|
| Agent | Agent.name | species <Agent.name> | Chaque Agent devient une espèce GAML. |
| Agent Spatialité | Agent.pos_x, Agent.pos_y | Attributs shape (ou position) | Utilisé pour définir la position initiale et la forme de l'espèce (si applicable). |
| Resource | Resource.name (Agent.holdsResources) | Attribut d'espèce (attribute) | Transformé en variable d'état de l'espèce (ex: float quantity_eau;). |
| Parameter | Parameter.name (Process.dependsOnParameters) | Variable Globale (global attribute) | Généralement défini en global car influençant plusieurs agents ou processus. |
| Hiérarchie | Agent.containsAgents | Héritage ou Relation GAML | Si la relation est simple, utilisez l'héritage d'espèces (ex: species A parent: B). |



#### II. Mapping des Processus Comportementaux (Ecore Process → GAML Action)

Les processus sont transformés en actions GAML (action), qui sont les unités de comportement exécutables par les espèces.

| Concept Source (Ecore) | Élément Source (Attribut/Référence) | Concept Cible (GAML) | Règle de Transformation |
|------------------------|------------------------------------|----------------------|-----------------------|
| Processus | Process.name | action <Process.name> | Chaque Processus devient une action GAML, rattachée à l'espèce de l'Agent isSubjectOf. |
| Logique Comportementale | Process.pseudoCode | Corps de l'action GAML | Le contenu du pseudoCode est copié/nettoyé et inséré dans le bloc de l'action GAML. (Nécessite une étape de "nettoyage" ou de traduction simple en syntaxe GAML dans Jinja2). |
| Déclenchement (Quand) | (Source JSON Externe) | Action de type reflex avec condition when | Si une triggerCondition est définie dans le JSON, elle est transformée en clause when dans la reflex GAML. |
| Flux de Mouvement | MovementProcess.source, MovementProcess.destination | Primitives GAML ask, move, goto | Traduit le ProcessusMouvement en une séquence d'instructions de déplacement GAML. |
| Flux de Transformation | TransformationProcess.affectsResources | Instructions GAML d'affectation | Traduit les changements de quantité (production/consommation) en expressions (ex: self.quantity_eau <- self.quantity_eau - 10;). |



#### III. Mapping des Données d'Initialisation et de Contexte (JSON → GAML)

Cette étape montre comment les sources de données externes (JSON/YAML) sont fusionnées dans la structure GAML.

| Concept Source (JSON) | Section JSON (Template) | Concept Cible (GAML) | Règle de Transformation |
|-----------------------|-------------------------|----------------------|-----------------------|
| Paramètres de Simulation | initializationTemplate.json (parameters) | Variables Globales (global attribute) | Utilisé pour définir les constantes et les paramètres d'expérimentation. |
| Valeurs Initiales | initializationTemplate.json (attributeValues) | Bloc init de l'espèce GAML | Fournit les valeurs de départ des attributs des agents (ex: float quantity_eau <- 100.0;). |
| Indicateurs | indicatorTemplate.json (formula) | Moniteur GAML (monitor ou output) | La formule de calcul est traduite en expression GAML et ajoutée au bloc d'affichage des résultats. |
| Instanciation | initializationTemplate.json (scenarios) | Instruction de création (create) dans le bloc init | Détermine le nombre d'agents à créer pour chaque espèce au début de la simulation (ex: create Eleveur number: 5;). |



### Schéma de Flux M2C pour le Moteur de Transformation

Le moteur M2C (Modèle vers Code) opérera en deux phases distinctes mais intégrées dans le code Python :

#### Phase d'Extraction et d'Assemblage (Python/lxml) :

- Lire le fichier XMI via lxml et extraire la hiérarchie.
- Lire les fichiers JSON (via json ou un parser YAML/CSV préliminaire) pour obtenir les données contextuelles.
- Assembler un Modèle Intermédiaire (M') : Créer des objets ou des dictionnaires Python unifiés qui contiennent toutes les informations (structure du XMI + initialisation du JSON) pour chaque espèce.

#### Phase de Génération (Python/Jinja2) :

- Utiliser le Modèle Intermédiaire (M') comme contexte pour rendre les templates Jinja2 (.gaml.jinja).
- Le template principal crée la structure de base du modèle GAML (définition des global, des experiment et de la model principale).
- Les templates secondaires itèrent sur M' pour générer dynamiquement les blocs species, les attributes, et les actions.

Cette approche garantit une séparation claire entre la logique d'extraction (Python/lxml) et la logique de présentation du code cible (Jinja2).


## Plan de travail (Pipeline)

L'ajout de tests à chaque étape (approche TDD ou Test-Driven Development appliqué à l'IDM) est essentiel pour valider la chaîne de transformation.

### Plan de Travail Détaillé : Moteur de Transformation XMI → GAML

#### Phase I : Fondation et Ingénierie du Modèle Intermédiaire (M')

L'objectif est d'assembler les données sources hétérogènes (XMI, JSON) en un modèle Python unifié (M') et de valider l'étape critique de parsing.

| Étape | Tâche à Réaliser | Livrable(s) | Tests / Validation (Critère de Succès) |
|-------|------------------|-------------|---------------------------------------|
| I.1 | Mise en Place du Parseur JSON/YAML | Script Python pour la lecture et la fusion des fichiers JSON/YAML/CSV vers une structure de données Python unique (dictionnaire). | Test JSON : Charger les 4 templates JSON. Vérifier que toutes les clés (e.g., parameters, scenarios, formula) sont accessibles et que les structures sont cohérentes. |
| I.2 | Conception du Modèle Intermédiaire (M') | Définition des classes/structures Python (e.g., AgentModel, ResourceModel, ProcessModel) qui recevront les données de l'XMI et des JSON. | Test Structure : Valider que la structure M' est optimisée pour la boucle de génération Jinja2 (e.g., M.agents est une liste itérable, chaque agent contient ses processus et ses ressources). |
| I.3 | Extraction du XMI (via lxml) | Fonction Python utilisant lxml pour naviguer dans le modeleElevage_en.xmi et mapper les entités Ecore vers les structures du Modèle Intermédiaire (M'). | Test XMI : S'assurer que tous les Agents, Resources, et Processus du XMI sont correctement extraits. Validation de l'Héritage : S'assurer que les TransformationProcess et MovementProcess héritent correctement de Process. |
| I.4 | Assemblage du Modèle Final (Fusion) | Fonction finale qui fusionne les données du M' (XMI) avec les valeurs d'initialisation et de comportement des sources JSON/YAML. | Test de Fusion : Pour un Agent donné, vérifier que ses attributs pos_x (du XMI) et sa valeur d'initialisation (du JSON) sont présents dans l'objet M' final. |



#### Phase II : Transformation de Code (M2C) via Jinja2

L'objectif est d'implémenter les règles de mapping définies en utilisant le moteur de templating Jinja2 et de générer un modèle GAML structurellement correct.

| Étape | Tâche à Réaliser | Livrable(s) | Tests / Validation (Critère de Succès) |
|-------|------------------|-------------|---------------------------------------|
| II.1 | Template Structurel GAML | Fichier main.gaml.jinja contenant la structure de base (déclaration du model, global, experiment, output). | Test de Base : Générer un fichier .gaml minimal. Vérifier que le code généré est syntaxiquement valide selon GAML (pas d'erreurs d'ouverture/fermeture de balises GAML). |
| II.2 | Templates des Espèces (Agents) | Template species.gaml.jinja pour générer le bloc species de chaque Agent (y compris l'héritage, les attributs et les initialisations). | Test d'Espèces : Générer le code GAML pour au moins trois Agents. Vérifier que leurs Ressources sont correctement déclarées comme attributs d'espèce et que l'initialisation est correcte (via les données du JSON). |
| II.3 | Templates Comportementaux (Processus) | Template action.gaml.jinja pour itérer sur les Processus de chaque Agent et générer les blocs action GAML. | Test de Comportement : Vérifier que les chaînes pseudoCode (du XMI) sont correctement insérées dans le corps des actions GAML. Valider que le mapping MovementProcess → primitives GAML (move, goto) fonctionne. |
| II.4 | Génération de l'Expérimentation | Template pour transformer les scenarios (JSON) et les indicators (JSON) en un bloc experiment GAML. | Test d'Expérimentation : Vérifier que les variables d'entrée (parameters du JSON) sont correctement mappées comme paramètres de l'expérience et que les formula des Indicateurs sont insérées dans les monitors ou les outputs. |



#### Phase III : Intégration, Nettoyage et Validation Finale

L'objectif est d'intégrer le moteur M2C dans l'environnement Python existant, d'améliorer la qualité du code généré et de valider l'exécution.

| Étape | Tâche à Réaliser | Livrable(s) | Tests / Validation (Critère de Succès) |
|-------|------------------|-------------|---------------------------------------|
| III.1 | Nettoyage du Pseudo-Code | Implémentation d'une fonction de pré-traitement Python pour normaliser/simplifier le pseudoCode (e.g., remplacer les opérateurs communs) avant l'injection Jinja2. | Test de Nettoyage : Vérifier que les chaînes de pseudoCode sont converties en syntaxe GAML sans erreur de syntaxe GAML pour les opérations de base (=, if, for). |
| III.2 | Intégration du Moteur M2C | Intégrer la logique de transformation (Phase I & II) dans le framework CLI existant (similaire à la manière dont le moteur de documentation est appelé). | Test d'Intégration : Lancer le moteur via la ligne de commande (python main.py --generate-gaml). S'assurer qu'un fichier .gaml complet est produit. |
| III.3 | Validation d'Exécution (Smoke Test GAMA) | Essayer de charger le fichier GAML généré dans la plateforme GAMA et vérifier l'absence d'erreurs de compilation GAML. | Test GAMA : Le fichier .gaml doit charger dans GAMA sans erreur et la simulation doit pouvoir être lancée (même si les résultats initiaux ne sont pas encore validés). (Validation du Code Cible) |
| III.4 | Documentation du Moteur M2C | Mise à jour du README.md avec le mode d'emploi, les dépendances et les options du nouveau moteur M2C. | Livrable Final. |

## La Phase IV : Implémentation

### 1. Structure du projet

```text
Model_GAML_Generator/
├── src/                          # Code source du moteur GAML
│   ├── parsers/                  # RÉUTILISATION/DUPLICATION : Analyseurs de fichiers
│   │   ├── xmi_parser.py         # Lecture du XMI (lxml)
│   │   ├── json_loader.py        # Module unifié pour le chargement des JSON/YAML/CSV
│   │   └── ...                   # Autres parsers si nécessaire
│   ├── model_intermediate/       # NOUVEAU : Structures du Modèle Intermédiaire (M') - (Phase I.2)
│   │   ├── structures.py         # Définition des classes AgentModel, ProcessModel, etc.
│   │   └── assembler.py          # Logique de fusion XMI + JSON (Phase I.4)
│   ├── generator/
│   │   ├── code_generator.py       # Le moteur Python (Jinja2 orchestration)
│   │   ├── templates/                # NOUVEAU : Fichiers Jinja2 (.gaml.jinja) - (Phase II)
│   │   │   ├── model_main.gaml.jinja # Template principal (global, experiment, init)
│   │   │   ├── species.gaml.jinja    # Template pour les espèces (attributs, ressources)
│   │   │   ├── action.gaml.jinja     # Template pour les actions (processus, pseudoCode)
│   │   │   └── outputs.gaml.jinja    # Template pour les indicateurs (monitors)
│   │   └── transformer.py            # NOUVEAU : Moteur principal de transformation (remplace doc_builder.py)
├── input/                        # RÉUTILISATION : Fichiers d'entrée (identiques)
│   ├── introduction.yml          # Données pour les globales
│   ├── modele_conceptuel.xmi     # Le Modèle Source
│   ├── initialisation.csv        # Données pour l'initialisation et les scénarios
│   ├── indicators.csv            # Données pour les outputs/monitors
│   ├── user_manual.yml           # Données pour la structure de l'expérimentation
│   └── initialization_data/      # Fichiers CSV d'initialisation détaillés
├── output/                       # NOUVEAU : Fichiers GAML générés
│   └── modele_elevage.gaml       # Fichier de sortie GAML
├── tests/                        # NOUVEAU : Dossier pour les tests unitaires (crucial pour le plan)
│   ├── test_parsers.py           # Tests de lecture XMI et JSON (Phase I.3)
│   └── test_transformation.py    # Tests d'intégrité du code GAML généré (Phase II.4)
├── config.json                   # Configuration principale
└── main.py                       # Point d'entrée de l'application
```

### 2. Phase I : Fondation et Ingénierie du Modèle Intermédiaire (M')

#### 2.1 Phase I.1 & I.3 et prépare la structure de Modèle Intermédiaire (M')

##### - xmi_parser.py (Parser du Modèle Structurel)
Ce module utilise `lxml` et les expressions **XPath** pour naviguer dans l'arbre XMI et extraire les Agents, les Processus et les Ressources, en mappant leurs attributs Ecore vers une structure Python simple.

##### - json_loader.py (Chargeur Unifié des Données Externes)
Ce module centralise la lecture des différents formats (YAML, CSV, JSON) en s'appuyant sur la logique métier complexe que vous avez déjà développée dans vos parsers de documentation.

Attention : Dans une implémentation réelle, les classes et fonctions complexes comme `CSVToJSONConverter` ou `load_indicator_csv` (qui est dans `parser_csv_to_json_indicator.py`) devront être importées ou copiées/collées dans ce module pour être réutilisées. Par souci de concision, le code ci-dessous simule l'appel à votre logique existante.

#### 2.2 Phase I.2 : Conception du Modèle Intermédiaire (M')

L'objectif de la **Phase I.2** est de définir les structures de données Python (le Modèle Intermédiaire M') qui serviront de schéma unique pour l'injection dans les templates `Jinja2`. Ce modèle doit être capable d'accueillir et d'organiser les données hétérogènes provenant à la fois du XMI (structure) et des JSON/CSV (comportement, initialisation).

##### - Définir des classes Python
Définir des classes Python claires et orientées objet, qui reflètent fidèlement la sémantique de notre métamodèle Ecore. Ces classes seront implémentées dans le fichier `src/model_intermediate/structures.py` 

Le Modèle Intermédiaire sera articulé autour d'un conteneur racine unique, le SocioEcosystemModel, qui agrège les trois entités principales du modèle.

#### 2.3 Phase I.4 (Assemblage/Fusion)

La Phase I.4 (src/model_intermediate/assembler.py) aura pour tâche principale de :

- Créer une instance de SocioEcosystemModel.
- Remplir les dictionnaires self.agents, self.properties, et self.processes avec les données de l'XMIParser.
- Utiliser les clés de référence (e.g., heldBy_refs, isSubjectOf_refs) pour ré-établir les liens sémantiques entre les objets (ex: attacher un objet PropertyModel à la liste AgentModel.attributes).
- Itérer sur les données du UnifiedJSONLoader et mettre à jour les attributs fusionnés (e.g., AgentModel.initial_count, ProcessModel.trigger_condition) en utilisant l'ID comme clé de jointure.


### 3. Phase II : Transformation de Code (M2C) via Jinja2

#### 3.1  Objectif de la Phase II

**Transformer le modèle intermédiaire `SocioEcosystemModel` (M') en un fichier GAML complet, exécutable dans GAMA.**

##### On va :

1. **Créer une structure de templates Jinja2**  
   → Modulaire, maintenable

2. **Implémenter un `GamlGenerator` qui :**
   - Charge les templates
   - Injecte les données de M'
   - Génère `model.gaml` dans `output/`

3. **Gérer tous les éléments clés :**

   | Élément         | Description |
   |-----------------|-------------|
   | `global`        | `init`, paramètres, config spatio-temporelle |
   | `species`       | Agents → `Parcel`, `Herd`, etc. |
   | `init`          | Création d’agents, valeurs initiales |
   | `reflex` / `action`        | Actions → processus |
   | `experiment`    | GUI + indicateurs |


*Objectif final : un fichier `model.gaml` 100 % fonctionnel, généré automatiquement à partir du modèle intermédiaire.*


#### 3.2 Structure du Répertoire 

```text
Model_GAML_Generator/
├── src/
│   └── gaml_generator/
│       ├── __init__.py
│       ├── generator.py
│       └── templates/
│           ├── global.j2
│           ├── species.j2
│           ├── init.j2
│           ├── reflex.j2
│           └── experiment.j2
├── output/                  ← model.gaml sera généré ici
└── tests/
    └── test_gaml_generator.py
```

```text
***deepseek***
templates/
├── main.j2                    # Template principal unifié
├── partials/
│   ├── globals.j2            # Bloc global
│   ├── species.j2            # Définition des espèces
│   ├── init.j2               # Initialisation
│   ├── reflexes.j2           # Réflexes globaux
│   └── experiment.j2         # Expérimentation et outputs
```

Structure Fichiers GAML :
```text
***deepseek***
model.gaml                    # Fichier principal (imports)
├── globals.gaml             # Paramètres globaux et constantes
├── species/                 # Dossier des espèces
│   ├── farmer.gaml
│   ├── animal.gaml
│   └── pasture.gaml
├── behaviors/               # Comportements et réflexes
│   ├── movement.gaml
│   └── transformation.gaml
├── experiments/             # Configurations expérimentales
│   ├── baseline.gaml
│   └── sensitivity.gaml
└── outputs/                 # Indicateurs et visualisations
    ├── charts.gaml
    └── monitors.gaml
```

#### 3.2 Implémentation du Moteur de Génération
##### - Le Moteur Python : `src/generator/code_generator.py`
Ce module est responsable de charger l'environnement Jinja2 et d'appeler le template principal en lui passant l'intégralité du modèle intermédiaire (M').

##### - Les Templates Jinja2 (`src/generator/templates/`)
La robustesse ici est assurée par l'utilisation de macros et de la logique conditionnelle pour gérer l'héritage et l'initialisation.

##### - `src/generator/templates/main_model.gaml.j2` (Le Squelette Principal)
Ce template assemble les sous-sections.


##### - `src/generator/templates/_species_block.gaml.j2` (Héritage et Attributs)
Ce template est crucial pour la robustesse des espèces :

Héritage : Utilise le champ partOfParentAgent_ref de l'Agent PIM.

Attributs : Gère les Resources et Parameters avec leurs types GAML correspondants.

Actions : Intègre les Processus GAML.


##### - `src/generator/templates/_globals_block.gaml.j2` (Variables Globales)
Ce template gère la configuration globale et les paramètres.


#### 3.3 La phase II.2 : Stratégie pour la Traduction du Pseudo-Code

La traduction du `pseudoCode` des Process XMI en `actions` ou `réflexes` GAML est en effet le défi le plus critique et la clé de la réussite. C'est l'étape où le `Modèle Indépendant de la Plateforme` (PIM) est transformé en `Modèle Spécifique à la Plateforme` (PSM) GAMA.

##### ----- Manuel d’utilisation du standard PseudoCode pour GAMA  


Ce document décrit le format standardisé adopté pour écrire les pseudoCodes dans les attributs `pseudoCode` des processus (élément `<ses:processes>` dans le XMI).

**L’objectif est de rendre le pseudoCode :**

- Facile à parser automatiquement
- Peu ambigu (pas de dépendance à l’indentation)
- Proche de la syntaxe GAML finale
- Facile à relire et maintenir par les humains

##### Règles principales du standard

| Règle | Description | Exemple correct | Exemple incorrect (à éviter) |  Commentaires  |
|-------|-------------|------------------|-------------------------------|----------|
| 1     | Pas de mot-clé `then` | Supprimer systématiquement `then` après les conditions `if` | `if (x > 0) { ... }` | `if x > 0 then ...` |
| 2     | Parentheses obligatoires autour de la condition | Toujours `( )` autour de l’expression booléenne | `if (temp < 5) { ... }` | `if temp < 5 { ... }` |
| 3     | Blocs délimités par `{ }` | Toujours utiliser `{` et `}` même pour une seule instruction | `if (a) { b = 1; }` | `if (a) b = 1;` |
| 4     | Une instruction par ligne dans les blocs | Sauf cas très courts et évidents | `temp = 10;`<br>`factor = exp(temp);` | `temp = 10; factor = exp(temp);` (sur une ligne) |
| 5     | Commentaires | Utiliser uniquement `//` (en début ou fin de ligne) | `// Étape 1`<br>`k = 0.5; // taux de base` | `/* commentaire */` (sauf dans les annotations `resource_xxx`) |
| 6     | Annotations de ressources/propriétés | Garder le format existant | `leaf_litter /* resource_006 */` | `leaf_litter [resource_006]` |
| 7     | Opérateurs de comparaison | Utiliser les symboles standards XML-friendly quand dans XML | `<` → `&lt;`<br>`>` → `&gt;`<br>`<=` → `&lt;=`<br>`>=` → `&gt;=` | Utiliser `<` directement dans l’attribut (sera encodé par le XML) |
| 8     | Pas de point-virgule après un bloc | Pas de `;` après la fermeture `}` | `if (x) { y++; }`<br>`z = 3;` | `if (x) { y++; };` |
| 9     | Indentation | Pure convention visuelle (2 ou 4 espaces) – ne pas compter dessus pour le parsing | (indentation libre mais cohérente) | (ne pas écrire de code qui casse si on supprime les espaces) |
| 10    | Assignations composées | `+=`, `-=`, `*=`, `/=` autorisés | `stock += flux;`<br>`n -= consumed;` | (OK) |

- **Paramètres globaux** :

Correspondent aux dependsOnParameters dans ton XMI.

Doivent être déclarés dans le préambule GAMA (global { float k_base <- 0.0; }).

- **Variables d’état (resources)** :

Correspondent aux involvedResources et affectsResources.

Doivent être déclarées dans les species GAMA (species Soil { float soil_nitrogen <- 0.0; }).

- **Variables locales** :

Restent internes aux actions ou réflexes, pas besoin de déclaration globale.

## Exemple complet (format standard)

```text
// Étape 1 : Calcul du facteur environnemental (k)
soil_temp = soil_temperature /* resource_063 */;
temp_factor = exp(0.069 * (soil_temp - 10));

if (temp_factor < 0) {
  temp_factor = 0;
}

soil_moisture = soil_moisture /* resource_053 */;
field_capacity_tmp = field_capacity /* resource_005 */;
moisture_factor = soil_moisture / field_capacity_tmp;

if (moisture_factor > 1) {
  moisture_factor = 1;
}
if (moisture_factor < 0.2) {
  moisture_factor = 0;
}

// Étape 2 : Taux de minéralisation effectif
k_base = base_mineralization_rate_k_base /* property_033 */;
k = k_base * temp_factor * moisture_factor;

rate = k * time_step;           // proportion minéralisée par pas de temps

// Étape 3 : Mise à jour des stocks
leaf_litter /* resource_006 */ -= min(leaf_litter * rate, leaf_litter);
soil_nitrogen /* resource_001 */ += 2.5 * rate;
```

**Conseils pour l’écriture**

- Toujours mettre des { } même pour une seule ligne → cela évite 90 % des erreurs de parsing
- Préférer des noms de variables explicites même s’ils sont un peu longs
- Grouper logiquement les calculs par étape avec des commentaires // Étape X
- Tester mentalement : « Si je supprime toute l’indentation, est-ce que le code reste compréhensible ? » → si non → ajouter des { }
- Éviter les imbrications trop profondes (> 3 niveaux) sans commentaire clair
- Library parsimonious ou pyparsing pour définir une syntaxe pseudoCode (e.g., if_stmt = "if" expr "then" (stmt | block), block = indented_stmts)
- Le parsing futur (regex ou tokenizer simple suffira souvent)



#### Choix approches de parsing pour ton pseudo-code → GAMA

##### 1. Tokenizer Manuel + Compteur d'Accolades (Approche DIY Basique)

**Description** : On tokenise le code ligne par ligne (split sur espaces, ponctuation), on compte les `{ }` pour détecter les blocs, et on reconstruit un AST simple (arbre abstrait) manuellement.

**Pros** :
- Très léger : Pas de dépendance externe (juste `re` et `collections`)
- Rapide à implémenter pour ton cas simple (assignations et `if` avec `{ }`)
- Performant pour de petits codes

**Cons** :
- Peu robuste aux variations (ex. espaces irréguliers, expressions imbriquées comme `min(1, max(0, x))`, ou erreurs comme `{` non fermée)
- Erreur-prone : Gérer les imbriquations, les commentaires, les strings entre `"` demande beaucoup de regex custom → bugs fréquents
- Pas industriellable : Difficile à étendre (ex. si tu ajoutes `while` ou `switch` plus tard), pas de grammaire formelle pour valider le code, et maintenance lourde
- Pas de support natif pour parsing récursif (ex. expressions mathématiques complexes)

**Score pour ton projet** : **4/10**  
OK pour un PoC rapide, mais **pas scalable** pour un générateur GAMA fiable (risque de faille sur des pseudoCodes variés).

##### 2. Pyparsing

**Description** : Bibliothèque Python pure pour définir des grammaires BNF-like, qui parse en AST directement.

**Pros** :
- Robuste pour les langages structurés comme le tien (`if`, blocs `{ }`, expressions)
- Erreur handling intégré : Rapporte les positions d'erreurs (ex. "accolade non fermée ligne 5")
- Extensible : Facile d'ajouter des règles pour `for`, fonctions, etc.
- Industrialisable : Utilisée dans des projets pros (ex. config parsers, DSL)

**Cons** :
- Verbose à définir : La grammaire se définit avec beaucoup de code Python  
  (ex. `if_stmt = Keyword("if") + LPAREN + expr + RPAREN + LBRACE + stmt_list + RBRACE`)
- Performance moyenne pour des codes très longs (mais OK pour tes pseudoCodes courts)
- Courbe d'apprentissage : Un peu plus "bas niveau" que Lark

**Score pour ton projet** : **8/10**  
Solide, mais un peu heavy pour un standard simple comme le tien.

##### 3. Lark

**Description** : Bibliothèque moderne pour parsers (utilise EBNF pour définir la grammaire en string, parse en arbre ou transforme directement).

**Pros** :
- Très facile à définir : Grammaire en texte clair  
  (ex. `if_stmt: "if" "(" expr ")" "{" stmt* "}"`), rapide à itérer
- Robuste et sans faille : Supporte ambiguïtés, erreur recovery, et validation automatique  
  Parser LALR/Earley pour efficacité
- Industrialisable : Utilisée en prod (ex. pour DSL, JSON parsers custom)  
  Facile à tester (grammaire séparée du code), extensible (ajouter des règles en 1 ligne), et intégrable avec transformers pour générer du GAML directement (ex. visitor qui traduit l'AST en code GAMA)
- Performant : Rapide même pour des codes plus complexes, et léger (dépendance minimale)
- **Bonus pour GAMA** : On peut définir un transformer qui mappe directement  
  `"if (cond) { stmt }"` → `"if cond { stmt }"` en GAML (avec ajustements pour `< >`, etc.)

**Cons** :
- Nécessite une dépendance externe (`pip install lark`)
- Si la grammaire est mal définie, debugging peut prendre un peu de temps (mais moins que pyparsing)

**Score pour ton projet** : **9/10**  
Idéal pour robustesse + industrialisation. **C'est ce que je recommande** pour des projets comme le tien (génération de code à partir d'un DSL simple).

## Recommandation Finale

Je recommande **Lark** pour plusieurs raisons :

- **Robustesse** : Gère les erreurs (ex. lève exception avec ligne/colonne si `{ }` non équilibré ou condition sans `(` `)`) → évite les fails silencieux
- **Industriellable** : Grammaire en EBNF est lisible/maintenable (tu peux la versionner séparément), facile à scaler si ton pseudoCode évolue (ex. ajouter arrays, fonctions)
- **Efficacité pour GAMA** : On peut implémenter un "transformer" qui génère directement le GAML  
  (ex. remplace `AND` par `"and"`, ajoute `::` pour annotations, etc.)
- **Transition facile** : Compatible avec ton nettoyage actuel (on applique Lark sur le code nettoyé)
- **Comparé aux autres** : Plus moderne et moins verbose que pyparsing ; plus puissant et moins fragile que le manuel

```text
PseudoCodeCleaner (→ texte nettoyé + validé)
      ↓
Lark Parser (→ AST avec grammaire EBNF)
      ↓
VariableTracker (Transformer Lark : parcourt l’AST → collecte variables + types + annotations)
      ↓
GamlASTTranslator (Transformer Lark : traduit chaque nœud AST en ligne GAML)
      ↓
GamlEmitter (Assemble les déclarations + code traduit + imports GAML)
      ↓
ProcessToGAMLConverter (Orchestre le tout pour un processus donné)
```


1. PseudoCodeCleaner
→ Rôle : Nettoyage + validation stricte du standard
→ Entrée : texte brut du XMI
→ Sortie : texte nettoyé (conforme ou erreur levée)
→ Statut : À refondre (j’ai déjà proposé une version dans un message précédent)
2. Lark Parser (nouveau composant central)
→ Définit la grammaire EBNF du standard pseudoCode
→ Produit un AST (arbre abstrait)
→ Lève des erreurs précises si non conforme (ex. accolade manquante, then présent, condition sans ( ))
3. VariableTracker (évolué)
→ Traverse l’AST pour collecter toutes les variables assignées
→ Détecte les variables de boucle (for each var in ...)
→ Infère types + scopes (global/local)
→ Génère les déclarations float var <- 0.0;
4. GamlASTTransformer (successeur de GamlLineTranslator)
→ Visite l’AST (via lark.Transformer)
→ Produit les lignes GAML indentées (le « translated_body »)
→ Gère automatiquement l’indentation, traduit AND → and, etc.
5. GamlEmitter (quasi inchangé)
→ Reçoit : déclarations + translated_body + métadonnées XMI
→ Assemble le bloc final action ... { ... } + reflex optionnel
6. ProcessToGAMLConverter (légèrement adapté)
→ Orchestre : Cleaner → Lark Parser → VariableTracker → GamlASTTransformer → GamlEmitter
→ Gère les erreurs de parsing de façon centralisée

```text
pseudocodeToaction/
├── pseudocode_cleaner.py          # Version avec détection ; manquants
├── lark_parser.py                 # Nouveau : LarkPseudoCodeParser
├── variable_tracker.py            # Version refondue sur AST
├── gaml_ast_transformer.py        # Nouveau : GamlASTTransformer
└── gaml_emitter.py                # Version mise à jour
```


Pour assurer une solution générique et robuste, notre analyse du pseudo-code va se concentrer sur les éléments suivants qui devront être traduits en syntaxe GAML :

- **Syntaxe GAMA ciblée** : Déterminer si un Process XMI génère un **reflex** (exécution cyclique, sans arguments) ou une **action** (bloc de code appelé par un autre Process ou Agent).

  * les affectations
  * les blocs conditionnels
  * les boucles
  * les déclarations de variables
  * la capitalisation

- **Structures de Contrôle** : Identifier les patrons de code (boucles **FOR/WHILE**, conditions **IF/ELSE**, etc.).

- **Références aux Entités/Variables** : S'assurer que les noms de variables (**PropertyModel**), de paramètres (**Parameter**), et les agents (**AgentModel**) sont correctement référencés dans le code GAML généré (ex: `self.variable` ou `target_agent.variable`).

- **Opérations Spécifiques** : Repérer les opérations mathématiques, spatiales, ou spécifiques au domaine qui nécessiteront une fonction GAML particulière (ex: `one_of()`, `ask`, etc.).
 

##### 3.3 Différence entre `reflex` et `task` (action) en GAML

En **GAML**, les concepts de **`reflex`** et **`task`** (ou `action`) servent tous deux à définir un comportement, **mais ils opèrent à des niveaux de contrôle très différents**.

##### Comparaison des caractéristiques

| Caractéristique       | `reflex`                                                                 | `task` (action)                                                                 |
|-----------------------|--------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Objectif**          | Activer un comportement **à chaque pas de temps (cycle)** si une condition est remplie. | Définir une **séquence d'instructions** qui peut être **appelée**.              |
| **Exécution**         | **Automatique et périodique**. Évalué et exécuté à chaque pas de simulation. | **Manuelle et sur demande**. Doit être appelée explicitement via `do nom_task;`. |
| **Périodicité**       | **Cyclique** (souvent à chaque pas, ou selon une période définie).        | **Non cyclique** ; exécutée **une seule fois par appel**.                       |
| **Syntaxe**           | Déclaré avec `reflex`. Peut inclure `when:`.                             | Déclaré avec `task` (ou `action`).                                              |
| **Analogie**          | *Le cœur de l’agent* : « Je vérifie si je dois faire X, et je le fais. » | *Le cerveau de l’agent* : « Voici la procédure pour faire X. »                  |

---

##### A. Le `task` (ou `action`) : **La Définition du Savoir-Faire**

Une `task` est une **procédure encapsulée**. Elle regroupe un ensemble d'instructions GAML sous un **nom unique**.

**Rôle**
- Organiser le code.
- Rendre les comportements **réutilisables** et **lisibles**.

**Exemple dans notre modèle**

```gaml
task se_deplacer {
    point nouvelle_cible <- any_location_in(shape); 
    do move to: nouvelle_cible speed: 1.0; 
}
```

***Cette tâche ne s'exécute pas seule — elle doit être appelée.***


##### B. Le reflex : Le Moteur du Comportement
Un `reflex` est un **mécanisme d'activation**. C’est le principal moyen d’introduire de la dynamique dans un agent : il est évalué automatiquement par le moteur GAMA à chaque pas de temps.

**Rôle**

 - Déclencher des task, des action, ou des instructions.
 - Souvent conditionné avec when:.

**Exemple dans notre modèle**
```gaml
reflex deplacement_cyclique {
    do se_deplacer; // Le réflexe appelle la tâche
}
```
***avec condition***
```gaml
reflex manger when: energie < 50.0 { 
    // S'exécute seulement si l'énergie est faible
    do recharger_energie; 
}
```

Les concepts de reflex et task sont des éléments fondamentaux du GAML, définis dans :

```text
GAMA Platform Documentation – GAML Reference (Section Agent/Species Behavior)
C’est la source principale pour la distinction entre :

la structure comportementale (actions/tasks)
et l’activation périodique (reflex).

La traduction du pseudoCode en action GAML et son appel par un reflex constituent la stratégie la plus robuste et générique pour séparer la logique (l'Action, réutilisable) du déclencheur (le Reflex, temporel ou conditionnel).
```

##### C. Structure GAML : Action et Reflex pour un Processus

**L'Action GAML (Le Corps Logique)**

L'Action contient la traduction directe du **pseudoCode**. Elle doit être générée avec le **même nom que le Processus** (normalisé, ex. `mineralization`).

| Élément | Structure GAML | Rôle |
|---------|----------------|------|
| **Processus XMI (mineralization)** | `action mineralization { ... }` | Contient la logique complète de la dynamique. Elle peut recevoir des arguments (`action action_name param: type`) si le processus XMI en nécessite. |

**Le Reflex GAML (Le Déclencheur Temporel/Comportemental)**

Le **Reflex** est le mécanisme GAML qui garantit que le processus s'exécute **à chaque pas de temps** ou **sous une condition spécifique**.

| Élément | Structure GAML | Rôle |
|---------|----------------|------|
| **Reflex du Processus** | `reflex mineralization_dynamics when: (condition) { do mineralization; }` | Assure l'exécution cyclique de l'Action. Pour un processus fondamental comme `mineralization`, il est souvent un **réflexe simple**, ou conditionné par un drapeau `when: model_is_running`. |

##### D. Tableau des Règles de Transformation : Pseudo-code → GAML → NetLogo

Ce tableau est complété avec les structures de contrôle et les opérateurs communs en programmation, assurant la robustesse demandée.

###### D.1. Structures de Base et Opérateurs

| Pseudo-Code Pattern | Règle de Transformation | Code GAML | Code NetLogo | Notes |
|---------------------|-------------------------|-----------|----------------------------|-------|
| `// Comment` | Conservation | `// Comment` | `; Comment` | |
| `variable = expression;` | Utiliser l'opérateur d'affectation GAML. | `variable <- expression;` | `set variable expression` | `variable` doit être un attribut déclaré ou une variable locale (`float temp <- 0.0;`). |
| `variable += change;` ou `variable -= change;` | Traduction explicite pour la robustesse. | `variable <- variable + change;` | `set variable variable + change` | Les opérateurs raccourcis (`++`, `+=`) existent mais l'explicite est plus sûr. |
| `var = func(arg1, arg2);` | Traduction directe. | `var <- func(arg1, arg2);` | `set var func arg1 arg2` | Pour les fonctions mathématiques standard (`exp`, `log`, etc.). |
| `variable /* resource_001 */` | Utiliser le nom normalisé de l'attribut/ressource. | `variable` | `variable` | Les identifiants (`/* ... */`) sont ignorés après validation du nom. |
| `val = clamp(val, min, max);` | Utiliser les fonctions de borne GAML. | `val <- min_of(max_of(val, min), max);` | `set val max (list min (min (list val max)))` | Assure que la valeur reste dans la plage. |
| `PRINT "message" + var;` | Utiliser la commande d'affichage GAML. | `write "message" + var;` | `print (word "message" var)` | |

```text
PseudoCode → GAML
=          → <- (assignation) ou = (déclaration)
==         → = (comparaison)
!=         → !=
and        → and
or         → or
^          → ^ (puissance)
```

###### D.2. Structures Conditionnelles

| Pseudo-Code Pattern | Règle de Transformation | Code GAML | Code NetLogo | Notes |
|---------------------|-------------------------|-----------|----------------------------|-------|
| `IF condition THEn action;` | Traduire en bloc conditionnel GAML. | `if (condition) { action; }` | `if condition [ action ]` | Remplacer `THEn` par la syntaxe `{}` GAML. |
| `IF condition THEn action1 ELSE action2;` | Traduire en bloc `if/else`. | `if (condition) { action1; } else { action2; }` | `ifelse condition [ action1 ] [ action2 ]` | |
| `ELSE IF condition` | Traduire directement. | `else if (condition) { action; }` | `ifelse condition [ action ] [ ... ]` *(enchaînement via `ifelse` imbriqués)* | |

###### D.3.  Structures de Boucle (Critique pour la Généricité)

| Pseudo-Code Pattern | Règle de Transformation | Code GAML | Code NetLogo | Notes |
|---------------------|-------------------------|-----------|----------------------------|-------|
| `FOR i = 1 TO N DO action;` | Utiliser la boucle itérative GAML. | `loop i from 1 to N { action; }` | `let i 1 while [ i <= N ] [ action set i i + 1 ]` | Utile pour répéter une action un nombre fixe de fois. |
| `WHILE condition DO action;` | Utiliser la boucle conditionnelle GAML. | `while (condition) { action; }` | `while [ condition ] [ action ]` | |
| `FOREACH agent IN set DO action;` | Utiliser la structure GAML `for each` ou `ask` (si modification). | `for each agent in set_of_agents { action; }` | `foreach set_of_agents [ current-agent -> ask current-agent [ action ] ]` | `set_of_agents` est une liste/un ensemble GAML. |
| `FOR_ALL agent IN set DO action;` | Utiliser l'opérateur `ask` pour les actions collectives et/ou modifiantes. | `ask set_of_agents { action; }` | `ask set_of_agents [ action ]` | Préférable au `for each` si l'action modifie l'état de l'agent. |

###### D.4. Interventions sur d'autres Agents (Interactions et Mouvements)

| Pseudo-Code Pattern | Règle de Transformation | Code GAML | Code NetLogo | Notes |
|---------------------|-------------------------|-----------|----------------------------|-------|
| `ASK agent_type TO action(args);` | Utiliser la commande d'`ask` ciblée. | `ask one_of(agent_type) { do action args; }` | `ask one-of agent_type [ action ]` | L'agent appelant est le `subjects_refs` du processus XMI. |
| `CREATE new_agent N;` | Utiliser la commande de création GAML. | `create new_agent number: N;` | `create-new_agent N [ ... ]` | Génère `N` nouvelles entités du type `new_agent`. |
| `MOVE TO location;` *(Processus de type Movement)* | Utiliser les commandes spatiales GAML. | `do wander;` ou `goto location;` | `move-to location` ou `random-walk` | Dépend de la complexité du `MovementProcess`. |





## Données

- [Introduction](#introductionjson)
- [Initialization](#initializationjson)
- [Indicators](#indicatorsjson)
- [User Manual](#user_manueljson)



### introduction.json

```json
{
  "version": "1.0",
  "metadata": {
    "titre": "Introduction",
    "auteur": "Équipe de modélisation",
    "date_creation": "2025-10-27",
    "modele_reference": "ModeleElevage_v1.0"
  },
  "principe_modelisation": {
    "question_recherche": {
      "formulation": "Quel est l'impact des investissements dans le pastoralisme au Sahel sur la résilience des ménages et leur contribution aux ODD ?",
      "explication": "Toute modélisation part d'une question structurée où :\n- X définit l’ensemble des scénarios d'investissements (ex. appui régional au pastoralisme) \n- Y l’ensemble des indicateurs de résilience et ODD (ex. sécurité alimentaire, action climatique) \n- Z le contexte du Sahel (variabilité climatique, systèmes pastoraux)"
    },
    "concepts_fondamentaux": {
      "entites": "Système structuré en agents (acteurs humains et naturels) et processus dynamiques",
      "attributs": [
        {
          "type": "parametres",
          "definition": "dont la valeur ne varie pas au fil de la simulation, ex. taux de reproduction"
        },
        {
          "type": "variables_etat",
          "definition": "dont la simulation fait varier la valeur au fil du temps, ex. stocks de ressources comme l'eau ou le fourrage"
        }
      ],
      "portee_attributs": [
        "globaux : partagés par tout le système (nous avons choisi de les décrire dans l’entité « SocioEcosystem »)",
        "locaux : partagés par entités de même type (ex. troupeaux)",
        "individuels : spécifiques à chaque entité (ex. cash d'un ménage)"
      ]
    },
    "relation_questions_modele": {
      "explication": "X ⊆ A, Z ⊆ A, X ∩ Z = ∅, X ∪ Z = A\nX est un sous-ensemble des attributs (de A) comme les investissements \nZ est un sous-ensemble des attributs disjoint de X comme le contexte climatique \nX union Z = A \nY est calculé à partir des attributs comme les indicateurs ODD",
      "implication": "Un choix différent de X et Z permet de répondre à d'autres questions avec le même modèle, ex. simuler divers scénarios d'appui au pastoralisme pour évaluer résilience et ODD"
    }
  },
  "modele_specifique": {
    "question_centrale": {
      "formulation": "Quel est l'impact des investissements d'un Projet Régional d’Appui au Pastoralisme au Sahel sur la résilience des ménages et les ODD ?",
      "domaine": "pastoralisme agroécologique",
      "echelle": "territoriale et régionale (Sahel)"
    },
    "diagrammes": [
      {
        "id": "question_recherche",
        "fichier": "C:/Users/tingo/source/repos/tingourosanogo/CIM-PIM_Transformation/CIM-PIM_Transformation/project_root/src/input/diagrammes/question.png",
        "legende": "Question de recherche schématisée",
        "description": "Sur la flèche diagonale, on représente qu’une combinaison (X) d'investissements et facteurs exogènes impacte les stocks de ressources pastoraux.\nEn bas à droite, les stocks sont des quantités de ressources pour usages (humains, troupeaux, écosystèmes).\nAu milieu en bas, un porteur de ressource (ex. ménage) est composé de divers stocks et met en œuvre une dynamique utilisant des ressources.\nA gauche, les investissements sont ensembles de schémas mis en œuvre par acteurs (individuels ou collectifs).\nAu milieu en haut, les facteurs exogènes influencent le système sans contrôle des acteurs."
      },
      {
        "id": "facteurs_exogenes",
        "fichier": "C:/Users/tingo/source/repos/tingourosanogo/CIM-PIM_Transformation/CIM-PIM_Transformation/project_root/src/input/diagrammes/facteurs.png",
        "legende": "Facteurs exogènes",
        "description": "Les facteurs exogènes sont un ensemble de facteurs influençant le système sans être contrôlés par les acteurs, ex. variabilité climatique, prix marchés."
      }
    ],
    "composants_principaux": [
      {
        "nom": "porteurs_ressources",
        "description": "Composé de stocks (ex. eau, fourrage) et met en œuvre des dynamiques",
        "role": "Utilisent des ressources et produisent des stocks pour résilience"
      },
      {
        "nom": "schemas_gestion",
        "description": "Ensembles de schémas mis en œuvre par acteurs",
        "types": [
          "individuels : par ménages éleveurs",
          "collectifs : par villages ou institutions"
        ]
      },
      {
        "nom": "stocks",
        "description": "Quantités de ressources pour usages",
        "usages": [
          "humains (ex. cash)",
          "animaux (ex. troupeaux)",
          "plantes (ex. couvert herbacé)",
          "processus biophysiques (ex. sol)"
        ]
      }
    ],
    "acteurs": [
      {
        "type": "individuels",
        "exemple": "ménages éleveurs"
      },
      {
        "type": "collectifs",
        "exemple": "villages, institutions gouvernementales"
      }
    ]
  },
  "contextualisation": {
    "domaine_application": "modélisation socio-écosystème pastoral au Sahel",
    "pertinence_scientifique": "Permet d'évaluer impacts d'investissements sur résilience et ODD (ex. 2, 13, 15) dans un contexte de changement climatique et variabilité",
    "public_cible": [
      "décideurs politiques et investisseurs régionaux",
      "chercheurs en agroécologie et modélisation",
      "acteurs territoriaux (ménages, villages)"
    ]
  },
  "references_bibliographiques": [
    {
      "auteur": "World Bank",
      "annee": 2025,
      "titre": "Reinforcing pastoralism in the Sahel and West Africa: a decade of progress and the path forward",
      "journal": "World Bank Blogs"
    },
    {
      "auteur": "Snapp et al.",
      "annee": 2021,
      "titre": "Introducing experiences from African pastoralist communities to support future climate change adaptation in Asia",
      "journal": "Global Food Security"
    },
    {
      "auteur": "GIZ",
      "annee": 2022,
      "titre": "What can we learn from pastoral systems in Africa's drylands?",
      "edition": "GIZ Policy Brief"
    },
    {
      "auteur": "Bluesquare",
      "annee": 2025,
      "titre": "A Data-Driven Platform Supporting Pastoralism in the Sahel Region",
      "journal": "Bluesquare Hub"
    },
    {
      "auteur": "Ndiaye et al.",
      "annee": 2021,
      "titre": "Resilience strategies of West African pastoralists in response to scarcity of pastoral resources: evolution of livestock herds and purchase of feed",
      "journal": "Pastoralism"
    },
    {
      "auteur": "World Bank",
      "annee": 2024,
      "titre": "Sahel RESILAND - World Bank Overview",
      "edition": "World Bank Programs"
    },
    {
      "auteur": "CARE",
      "annee": 2024,
      "titre": "CARE's Resilient Pastoral Livelihoods Framework",
      "edition": "CARE Climate Change"
    },
    {
      "auteur": "Böhm et al.",
      "annee": 2024,
      "titre": "Over-reliance on water infrastructure can hinder climate resilience in pastoral dryland populations",
      "journal": "Nature Climate Change"
    },
    {
      "auteur": "USAID",
      "annee": 2024,
      "titre": "Resilience and Economic Growth in the Sahel - Enhanced Resilience",
      "edition": "USAID Programs"
    },
    {
      "auteur": "Hänke et al.",
      "annee": 2019,
      "titre": "Land resources opportunities for a growing prosperity in the Sahel",
      "journal": "Current Opinion in Environmental Sustainability"
    }
  ]
}
```

### initialization.json
```json
{
  "metadata": {
    "protocol": "ODDv3",
    "model_name": "ModeleElevage",
    "version": "1.0.0",
    "creation_date": "2025-10-27",
    "last_modified": "2025-10-27",
    "authors": [
      {
        "name": "Équipe de modélisation",
        "affiliation": "Institution de Recherche Agroécologique",
        "role": "Expert Domaine Pastoralisme Sahel",
        "orcid": "0000-0000-0000-0000"
      },
      {
        "name": "Développeur Modèle",
        "affiliation": "Centre de Simulation",
        "role": "Développeur GAMA/NetLogo",
        "orcid": "0000-0000-0000-0001"
      }
    ],
    "references": [
      {
        "citation": "Grimm et al. (2020). The ODD protocol for describing agent-based and other simulation models: A second update to improve clarity, replication, and structural realism",
        "doi": "10.18564/jasss.4259"
      },
      {
        "citation": "World Bank (2024). Regional Sahel Pastoralism Support Project II (PRAPS-2)",
        "doi": "P173197"
      },
      {
        "citation": "Ndiaye et al. (2021). Resilience strategies of West African pastoralists",
        "doi": "10.1186/s13570-021-00210-8"
      }
    ]
  },
  "global": {
    "temporal_scope": {
      "start_date": "2020-01-01",
      "end_date": "2030-12-31",
      "time_step": "1 day",
      "warmup_period": "365 days"
    },
    "spatial_configuration": {
      "extent": [
        "-20",
        "10",
        "40",
        "25"
      ],
      "projection": "EPSG:4326",
      "resolution": "100 m"
    }
  },
  "input_data": {
    "spatial_data": [
      {
        "type": "raster",
        "format": "GeoTIFF",
        "path": "data/land_cover_sahel.tif",
        "description": "Land cover map for Sahel pastoral areas (ESA CCI)",
        "resolution": "100m",
        "source": "European Space Agency (ESA)",
        "uncertainty": "medium"
      },
      {
        "type": "vector",
        "format": "GeoJSON",
        "path": "data/water_points.geojson",
        "description": "Locations of water points and pastures",
        "source": "PRAPS Project Data / FAO",
        "reliability": "high"
      }
    ],
    "tabular_data": [
      {
        "type": "csv",
        "path": "data/household_survey_sahel.csv",
        "description": "Socio-economic survey on pastoral households (herd sizes, cash, resilience)",
        "sample_size": 2000,
        "response_rate": "75%",
        "validation_method": "cross_validation"
      }
    ]
  },
  "entities": [
    {
      "name": "HerdsmenHouseholds",
      "type": "agent",
      "count": 1500,
      "initialization_method": "data_driven",
      "data_source": "data/household_survey_sahel.csv",
      "sampling_strategy": "stratified_random",
      "stratification_variables": [
        "region",
        "herd_size_class"
      ],
      "attribute_mapping": [
        {
          "model_attribute": "cash",
          "data_field": "household_cash",
          "conversion": "none"
        },
        {
          "model_attribute": "herd_id",
          "data_field": "herd_identifier",
          "conversion": "none"
        }
      ]
    },
    {
      "name": "Herd",
      "type": "agent",
      "count": 150000,
      "initialization_method": "data_driven",
      "data_source": "data/household_survey_sahel.csv",
      "sampling_strategy": "proportional",
      "stratification_variables": [
        "species_composition"
      ],
      "attribute_mapping": [
        {
          "model_attribute": "herd_size",
          "data_field": "TLU_count",
          "conversion": "none"
        },
        {
          "model_attribute": "species_composition",
          "data_field": "species_ratio",
          "conversion": "parse_ratio"
        }
      ]
    },
    {
      "name": "WaterPoints",
      "type": "environment",
      "initialization_method": "gis_import",
      "data_source": "data/water_points.geojson",
      "attribute_mapping": [
        {
          "model_attribute": "capacity_m3",
          "data_field": "volume",
          "conversion": "none"
        },
        {
          "model_attribute": "water",
          "data_field": "water_level",
          "conversion": "liters_to_m3"
        }
      ]
    },
    {
      "name": "Parcel",
      "type": "environment",
      "initialization_method": "gis_import",
      "data_source": "data/land_cover_sahel.tif",
      "attribute_mapping": [
        {
          "model_attribute": "fodder_biomass",
          "data_field": "ndvi_value",
          "conversion": "ndvi_to_biomass"
        },
        {
          "model_attribute": "herbaceous_type",
          "data_field": "land_type",
          "conversion": "none"
        }
      ]
    },
    {
      "name": "GovernmentalInstitutions",
      "type": "agent",
      "count": 10,
      "initialization_method": "fixed",
      "data_source": "none",
      "attribute_mapping": [
        {
          "model_attribute": "policy_strength",
          "data_field": "none",
          "conversion": "fixed_value"
        }
      ]
    },
    {
      "name": "Markets",
      "type": "agent",
      "count": 50,
      "initialization_method": "gis_import",
      "data_source": "data/market_locations.geojson",
      "attribute_mapping": [
        {
          "model_attribute": "market_access",
          "data_field": "accessibility_index",
          "conversion": "none"
        }
      ]
    }
  ],
  "parameters": {
    "fixed": [
      {
        "name": "adult_female_reproduction_rate",
        "entity": "Herd",
        "value": 0.7,
        "unit": "ratio",
        "definition": "Annual reproduction rate for adult females in herd",
        "source": "Ndiaye et al. (2021) - Pastoralism; typical 0.6-0.8 in Sahel",
        "uncertainty": {
          "distribution": "normal",
          "std_dev": 0.1
        },
        "sensitivity_rank": "high"
      },
      {
        "name": "drought_mortality_rate",
        "entity": "Herd",
        "value": 0.15,
        "unit": "ratio",
        "definition": "Mortality rate of herd during dry season",
        "source": "Sandford (1983); adjusted for Sahel droughts",
        "validation": "field_surveys"
      },
      {
        "name": "fodder_consumption_per_TLU",
        "entity": "Herd",
        "value": 6.0,
        "unit": "kg DM/day",
        "definition": "Daily dry matter intake per Tropical Livestock Unit (TLU)",
        "source": "FAO (2021) - Livestock feed requirements in Sahel",
        "uncertainty": {
          "distribution": "uniform",
          "min": 5.0,
          "max": 7.0
        },
        "sensitivity_rank": "medium"
      },
      {
        "name": "water_need_per_head",
        "entity": "Herd",
        "value": 30.0,
        "unit": "liters/day",
        "definition": "Daily water requirement per head of livestock",
        "source": "World Bank (2024) - PRAPS water management",
        "validation": "empirical_data"
      }
    ],
    "variable": [
      {
        "name": "investment_scenario",
        "entity": "Global",
        "values": [
          "baseline",
          "water_infrastructure",
          "market_access",
          "health_services"
        ],
        "definition": "PRAPS investment scenarios (water, markets, health)",
        "source": "World Bank PRAPS-2 (2024)"
      },
      {
        "name": "climate_scenario",
        "entity": "Global",
        "values": [
          "RCP4.5",
          "RCP8.5"
        ],
        "definition": "IPCC climate scenarios for Sahel variability",
        "source": "IPCC AR6 (2022)"
      }
    ]
  },
  "state_variables": {
    "fixed_initialization": [
      {
        "name": "cash",
        "entity": "HerdsmenHouseholds",
        "value": 2000.0,
        "unit": "XOF",
        "distribution": "lognormal",
        "parameters": {
          "mean": 7.6,
          "sigma": 1.0
        },
        "source": "Household surveys Sahel (World Bank 2024; average 1000-5000 XOF)"
      },
      {
        "name": "herd_size",
        "entity": "Herd",
        "value": 50.0,
        "unit": "TLU",
        "distribution": "normal",
        "parameters": {
          "mean": 50.0,
          "std_dev": 20.0
        },
        "source": "Ndiaye et al. (2021); typical 20-100 TLU/household"
      },
      {
        "name": "nitrogen",
        "entity": "Parcel",
        "value": 50.0,
        "unit": "kg/ha",
        "distribution": "normal",
        "parameters": {
          "mean": 50.0,
          "std_dev": 10.0
        },
        "source": "FAO (2021); typical for Sahelian soils"
      },
      {
        "name": "carbon",
        "entity": "Parcel",
        "value": 1000.0,
        "unit": "kg/ha",
        "distribution": "normal",
        "parameters": {
          "mean": 1000.0,
          "std_dev": 200.0
        },
        "source": "FAO (2021); typical SOM in Sahelian pastures"
      }
    ],
    "variable_initialization": [
      {
        "name": "fodder_biomass",
        "entity": "Parcel",
        "values": [
          "low",
          "medium",
          "high"
        ],
        "distribution": "categorical",
        "probabilities": [
          0.4,
          0.4,
          0.2
        ],
        "source": "NDVI data ESA (2020-2024) for Sahel seasons"
      },
      {
        "name": "herbaceous_type",
        "entity": "Parcel",
        "values": [
          "natural_prairie",
          "cultivated_prairie"
        ],
        "distribution": "categorical",
        "probabilities": [
          0.8,
          0.2
        ],
        "source": "GIZ (2022); dominant natural prairies in Sahel"
      },
      {
        "name": "water",
        "entity": "WaterPoints",
        "values": [
          50.0,
          100.0,
          150.0
        ],
        "distribution": "uniform",
        "parameters": {
          "min": 50.0,
          "max": 200.0
        },
        "source": "PRAPS water point surveys (World Bank 2024)"
      },
      {
        "name": "tree_count",
        "entity": "Parcel",
        "values": [
          20,
          50,
          100
        ],
        "distribution": "uniform",
        "parameters": {
          "min": 20,
          "max": 100
        },
        "source": "XMI comment; typical 20-100 trees/ha"
      }
    ]
  },
  "scenarios": [
    {
      "name": "baseline",
      "description": "No additional investments, current trends",
      "based_on": "RCP4.5 + PRAPS baseline",
      "parameters": {
        "climate_change_scenario": "RCP4.5",
        "policy_intervention": "none"
      },
      "state_variables": {
        "initial_investment": 0.0
      },
      "validation_status": "calibrated"
    },
    {
      "name": "praps_investment",
      "description": "PRAPS investments (water, health, markets)",
      "based_on": "PRAPS-2 objectives + RCP2.6 mitigation",
      "parameters": {
        "climate_change_scenario": "RCP2.6",
        "policy_intervention": "full_support"
      },
      "state_variables": {
        "initial_investment": 5000.0
      },
      "validation_status": "plausible"
    },
    {
      "name": "climate_stress",
      "description": "High climate stress without support",
      "based_on": "RCP8.5 + no intervention",
      "parameters": {
        "climate_change_scenario": "RCP8.5",
        "policy_intervention": "baseline"
      },
      "state_variables": {
        "initial_investment": 0.0
      },
      "validation_status": "stress_test"
    }
  ],
  "traceability": {
    "data_quality": [
      {
        "parameter": "adult_female_reproduction_rate",
        "quality_score": 0.85,
        "assessment_method": "literature_review",
        "experts": [
          {
            "name": "Expert Pastoralisme",
            "confidence": "high"
          }
        ]
      },
      {
        "parameter": "fodder_biomass",
        "quality_score": 0.75,
        "assessment_method": "remote_sensing_validation",
        "experts": [
          {
            "name": "Expert GIS",
            "confidence": "medium"
          }
        ]
      }
    ],
    "uncertainty_quantification": [
      {
        "parameter": "drought_mortality_rate",
        "uncertainty_type": "aleatory",
        "magnitude": "high",
        "propagation_method": "monte_carlo"
      },
      {
        "parameter": "fodder_biomass",
        "uncertainty_type": "epistemic",
        "magnitude": "medium",
        "propagation_method": "sensitivity_analysis"
      }
    ],
    "sensitivity_analysis": {
      "planned_methods": [
        "SOBOL",
        "Morris"
      ],
      "parameters_included": "all",
      "software": "SALib"
    }
  },
  "validation": {
    "methods": [
      {
        "method_name": "historical_validation",
        "validation_date": "2025-01-01",
        "participants": 10,
        "period": "2010-2020",
        "metric": "Nash-Sutcliffe",
        "metric_value": 0.75,
        "threshold": 0.6,
        "result": "model_calibrated"
      },
      {
        "method_name": "gps_field_validation",
        "validation_date": "2024-06-01",
        "participants": 5,
        "period": "2020-2024",
        "metric": "mobility_accuracy",
        "metric_value": 0.8,
        "threshold": 0.7,
        "result": "transhumance_validated"
      }
    ]
  },
  "initialization_rules": [
    {
      "entity": "HerdsmenHouseholds",
      "rule": "cash ~ lognormal(7.6, 1.0)",
      "implementation": "numpy.random.lognormal(7.6, 1.0, n_households)",
      "assumptions": "Distribution based on Sahel household surveys (World Bank 2024)"
    },
    {
      "entity": "Herd",
      "rule": "herd_size ~ normal(50, 20); species_composition = categorical([0.5 cattle, 0.3 sheep, 0.2 goats])",
      "implementation": "random.normal(50, 20); random.choice(['cattle', 'sheep', 'goat'], p=[0.5, 0.3, 0.2])",
      "assumptions": "Initial herd size and composition from Sahel surveys (Ndiaye et al. 2021)"
    },
    {
      "entity": "WaterPoints",
      "rule": "water ~ uniform(50, 200)",
      "implementation": "random.uniform(50, 200)",
      "assumptions": "Seasonal variability in Sahel water points (PRAPS 2024)"
    },
    {
      "entity": "Parcel",
      "rule": "fodder_biomass ~ categorical([0.4 low, 0.4 medium, 0.2 high]); nitrogen ~ normal(50, 10); carbon ~ normal(1000, 200)",
      "implementation": "random.choice(['low', 'medium', 'high'], p=[0.4, 0.4, 0.2]); random.normal(50, 10); random.normal(1000, 200)",
      "assumptions": "Based on NDVI and soil data for Sahel (ESA 2020-2024, FAO 2021)"
    }
  ]
}
```

### indicators.json

```json
{
  "indicators": [
    {
      "id": "PA.01.01",
      "name": "Charge animale instantanée",
      "category": "Pastoralisme",
      "source": "Dutilly-Diane et al. (2007), Journal of Arid Environments; Ndiaye et al. (2021), Pastoralism",
      "description": "Nombre d'unités de bétail (UBT) par hectare de pâturage disponible. Indicateur clé de pression sur les ressources fourragères, adapté au Sahel pour évaluer la durabilité et la résilience face à la variabilité climatique.\n",
      "formula": "CA = (Nombre UBT) / (Surface pâturable * Facteur Saison)",
      "unit": "UBT/ha",
      "variables": [
        {
          "name": "nombre_ubt",
          "entity": "Troupeau",
          "definition": "Effectif converti en unité de bétail tropical, ajusté pour races saheliennes",
          "unit": "UBT"
        },
        {
          "name": "surface_paturage",
          "entity": "Espace",
          "definition": "Surface accessible au pâturage, incluant parcours transhumants",
          "unit": "ha"
        }
      ],
      "parameters": [
        {
          "name": "facteur_saison",
          "entity": "Système",
          "definition": "Coefficient saisonnier d'ajustement pour variabilité pluviométrique",
          "value": 1.2,
          "unit": "coefficient"
        }
      ]
    },
    {
      "id": "PA.02.01",
      "name": "Taux de rotation des pâturages",
      "category": "Pastoralisme",
      "source": "Vallentine (2001), Grazing Management; Snapp et al. (2021), Global Food Security",
      "description": "Fréquence de rotation des troupeaux entre parcelles. Critique pour la durabilité des parcours et la résilience aux sécheresses au Sahel.\n",
      "formula": "TR = (Nombre rotations) / (Période analysée)",
      "unit": "rotations/an",
      "variables": [
        {
          "name": "nombre_rotations",
          "entity": "Troupeau",
          "definition": "Nombre de déplacements entre parcelles, incluant transhumance",
          "unit": "n"
        },
        {
          "name": "periode_analyse",
          "entity": "Système",
          "definition": "Période d'observation, typiquement une année pastorale",
          "unit": "jours"
        }
      ],
      "parameters": [
        {
          "name": "duree_min_sejour",
          "entity": "Parcelle",
          "definition": "Durée minimale entre deux rotations pour régénération",
          "value": 21,
          "unit": "jours"
        }
      ]
    },
    {
      "id": "PA.03.01",
      "name": "Taux de charge soutenable",
      "category": "Pastoralisme",
      "source": "Sandford (1983), Management of Pastoral Development; Böhm et al. (2024), Nature Climate Change",
      "description": "Capacité de charge maximale sans dégradation à long terme. Basé sur la productivité fourragère, adapté aux impacts climatiques au Sahel.\n",
      "formula": "TCS = (Production fourragère annuelle) / (Consommation UBT)",
      "unit": "UBT/ha/an",
      "variables": [
        {
          "name": "production_fourrage",
          "entity": "Parcelle",
          "definition": "Biomasse fourragère produite annuellement, ajustée pour variabilité pluviométrique",
          "unit": "kg MS/ha"
        },
        {
          "name": "consommation_ubt",
          "entity": "Troupeau",
          "definition": "Besoin annuel moyen par UBT, incluant mobilité",
          "unit": "kg MS/UBT"
        }
      ],
      "parameters": [
        {
          "name": "facteur_resilience",
          "entity": "Ecosystème",
          "definition": "Coefficient de résilience des parcours face au climat",
          "value": 0.85,
          "unit": "coefficient"
        }
      ]
    },
    {
      "id": "AE.02.01",
      "name": "Taux de couverture végétale",
      "category": "Agroécologie",
      "source": "FAO (2021), Voluntary Guidelines for Soil Conservation; GIZ (2022), Policy Brief on Dryland Pastoral Systems",
      "description": "Pourcentage de sol couvert par la végétation vivante ou morte. Réduit l'érosion et améliore la résilience au Sahel.\n",
      "formula": "TCV = (Surface couverte / Surface totale) * 100",
      "unit": "%",
      "variables": [
        {
          "name": "surface_couverte",
          "entity": "Parcelle",
          "definition": "Surface avec couverture végétale",
          "unit": "ha"
        },
        {
          "name": "surface_totale",
          "entity": "Parcelle",
          "definition": "Surface totale observée",
          "unit": "ha"
        }
      ],
      "parameters": [
        {
          "name": "surface_observée",
          "entity": "Espace",
          "definition": "Surface échantillonnée",
          "value": 1.0,
          "unit": "ha"
        }
      ]
    },
    {
      "id": "CL.03.01",
      "name": "Bilan carbone",
      "category": "Climat",
      "source": "IPCC (2019), GHG Guidelines; World Bank (2024), RESILAND Overview",
      "description": "Émissions nettes de GES par hectare, évaluant contribution à ODD 13 au Sahel.\n",
      "formula": "(émissions - séquestration) / surface",
      "unit": "tCO2eq/ha/an",
      "variables": [
        {
          "name": "émissions",
          "entity": "Exploitation",
          "definition": "Émissions totales de GES, incluant entériques",
          "unit": "tCO2eq/an"
        },
        {
          "name": "séquestration",
          "entity": "Sol",
          "definition": "Carbone séquestré dans les sols pastoraux",
          "unit": "tCO2eq/an"
        }
      ],
      "parameters": [
        {
          "name": "surface",
          "entity": "Espace",
          "definition": "Surface agricole utile",
          "value": 1.0,
          "unit": "ha"
        }
      ]
    },
    {
      "id": "CL.03.02",
      "name": "Indice de résilience climatique",
      "category": "Climat",
      "source": "IPCC (2022), AR6 Report; USAID (2024), Resilience in Sahel",
      "description": "Capacité à maintenir la production sous stress climatique, lié à résilience des ménages.\n",
      "formula": "(production_reelle / production_potentielle) * 100",
      "unit": "%",
      "variables": [
        {
          "name": "production_reelle",
          "entity": "Exploitation",
          "definition": "Production effective en année stressante",
          "unit": "t/ha"
        },
        {
          "name": "production_potentielle",
          "entity": "Exploitation",
          "definition": "Production théorique optimale",
          "unit": "t/ha"
        }
      ]
    },
    {
      "id": "BD.04.01",
      "name": "Indice de biodiversité fonctionnelle",
      "category": "Biodiversité",
      "source": "Díaz et al. (2015), Nature; CARE (2024), Resilient Pastoral Livelihoods",
      "description": "Abondance relative d'espèces indicatrices, contribuant à ODD 15 au Sahel.\n",
      "formula": "Σ(abondance_espèce_i * poids_écologique_i)",
      "unit": "points",
      "variables": [
        {
          "name": "abondance_especes",
          "entity": "Écosystème",
          "definition": "Nombre d'individus par espèce",
          "unit": "individus/ha"
        }
      ],
      "parameters": [
        {
          "name": "poids_ecologique",
          "entity": "Système",
          "definition": "Valeur écologique de l'espèce",
          "value": 0.75,
          "unit": "coefficient"
        }
      ]
    },
    {
      "id": "BD.04.02",
      "name": "Indice de biodiversité",
      "category": "Biodiversité",
      "source": "CBD (2020), Biodiversity Indicators; Ndiaye et al. (2021), Pastoralism",
      "description": "Richesse spécifique normalisée, pour évaluer durabilité des pâturages.\n",
      "formula": "nombre_espèces / surface_reference",
      "unit": "espèces/ha",
      "variables": [
        {
          "name": "nombre_espèces",
          "entity": "Espace",
          "definition": "Espèces identifiées dans pâturages",
          "unit": "nombre"
        }
      ],
      "parameters": [
        {
          "name": "surface_reference",
          "entity": "Système",
          "definition": "Surface de référence",
          "value": 10.0,
          "unit": "ha"
        }
      ]
    },
    {
      "id": "RE.01.01",
      "name": "Indice de résilience des ménages",
      "category": "Résilience",
      "source": "USAID (2024), Resilience in Sahel; Böhm et al. (2024), Nature Climate Change",
      "description": "Mesure la capacité des ménages à absorber les chocs climatiques et économiques.\n",
      "formula": "(revenus_diversifies + accès_ressources + santé_troupeau) / 3",
      "unit": "indice (0-1)",
      "variables": [
        {
          "name": "revenus_diversifies",
          "entity": "Ménage",
          "definition": "Niveau de diversification des revenus",
          "unit": "[0-1]"
        },
        {
          "name": "accès_ressources",
          "entity": "Ménage",
          "definition": "Accès à eau et fourrage",
          "unit": "[0-1]"
        },
        {
          "name": "santé_troupeau",
          "entity": "Troupeau",
          "definition": "Santé du bétail",
          "unit": "[0-1]"
        }
      ],
      "parameters": [
        {
          "name": "seuil_resilience",
          "entity": "Système",
          "definition": "Seuil minimal pour résilience",
          "value": 0.6,
          "unit": "indice"
        }
      ]
    },
    {
      "id": "ODD.02.01",
      "name": "Indice de sécurité alimentaire",
      "category": "ODD 2",
      "source": "FAO (2021), Food Security Indicators; World Bank (2025), Pastoralism in Sahel",
      "description": "Mesure la contribution à ODD 2 via production lait/viande.\n",
      "formula": "(lait_produit + viande_produite) / besoins_ménage",
      "unit": "%",
      "variables": [
        {
          "name": "lait_produit",
          "entity": "Exploitation",
          "definition": "Lait produit annuellement",
          "unit": "litres"
        },
        {
          "name": "viande_produite",
          "entity": "Exploitation",
          "definition": "Viande produite annuellement",
          "unit": "kg"
        },
        {
          "name": "besoins_ménage",
          "entity": "Ménage",
          "definition": "Besoins nutritionnels annuels",
          "unit": "équivalent calorique"
        }
      ],
      "parameters": [
        {
          "name": "facteur_nutritionnel",
          "entity": "Système",
          "definition": "Facteur de conversion nutritionnel",
          "value": 1.0,
          "unit": "coefficient"
        }
      ]
    },
    {
      "id": "ODD.13.01",
      "name": "Émissions nettes GES",
      "category": "ODD 13",
      "source": "IPCC (2019), GHG Guidelines; CARE (2024), Pastoral Livelihoods",
      "description": "Émissions nettes, évaluant action climatique (ODD 13).\n",
      "formula": "émissions - séquestration",
      "unit": "tCO2eq/an",
      "variables": [
        {
          "name": "émissions",
          "entity": "Système",
          "definition": "Émissions totales GES",
          "unit": "tCO2eq/an"
        },
        {
          "name": "séquestration",
          "entity": "Sol",
          "definition": "Séquestration carbone",
          "unit": "tCO2eq/an"
        }
      ]
    },
    {
      "id": "ODD.15.01",
      "name": "Indice de dégradation des terres",
      "category": "ODD 15",
      "source": "UNCCD (2022), Land Degradation Indicators; GIZ (2022), Dryland Pastoral Systems",
      "description": "Mesure la dégradation des pâturages, contribuant à ODD 15.\n",
      "formula": "1 - (couverture_végétale / couverture_optimal)",
      "unit": "indice (0-1)",
      "variables": [
        {
          "name": "couverture_végétale",
          "entity": "Parcelle",
          "definition": "Pourcentage de couverture végétale",
          "unit": "%"
        }
      ],
      "parameters": [
        {
          "name": "couverture_optimal",
          "entity": "Système",
          "definition": "Couverture végétale optimale",
          "value": 70.0,
          "unit": "%"
        }
      ]
    }
  ]
}
```


### user_manuel.json



# Interface utilisateur

```text
GAMA_Generator/
├── setup_guide_gama.sh          ← Script interactif (inspiré de setup_guide.sh)
├── config_gama.json             ← Configuration centralisée (inspiré de config.json)
├── main_gama.py                 ← Point d’entrée principal (inspiré de main.py)
├── src/                         ← Votre pipeline existant (cleaner, parser, transformer, emitter…)
├── input/                       ← Dossier pour XMI + pseudo-codes
├── output_gaml/                 ← Code GAML généré
└── logs/                        ← Logs détaillés

```

## Fonctionnalités du nouveau setup

- **setup_guide_gama.sh** : guide interactif qui demande :
  * Chemin du fichier XMI
  * Dossier des pseudo-codes (ou création de templates)
  * Dossier de sortie GAML
  * Options (générer reflex ? minifier ? diagnostics détaillés ?)
  * Mise à jour automatique de config_gama.json

- **config_gama.json** : contient tout ce dont le générateur a besoin (chemins, options d’émission, diagnostics activés, etc.).

- **main.py** : charge le config, exécute le pipeline complet (Cleaner → Parser → Collector → Transformer → Emitter), affiche les diagnostics riches, génère le GAML monolithique/modulaire, et propose les exports.


## 1. config.json

### Quoi
Fichier de configuration central au format **JSON** qui pilote toute l'application de génération de documentation.

### Comment
- Contient les chemins d'entrée/sortie pour chaque section (*Introduction*, *Modele_Conceptuel*, etc.).
- Définit les formats (**YAML, JSON, CSV, XMI…**).
- Gère les paramètres d'export (**HTML, PDF, DOCX**) et les assets (**CSS, images**).
- Mis à jour automatiquement par `setup_guide.sh`.

### Squelette (extrait clé)

```json
{
  "paths": {
    "Introduction": { "input_path": "...", "format": "yaml", ... },
    "Modele_Conceptuel": { "input_path": "...", "format": "xmi" },
    ...
  },
  "export": {
    "formats": ["html", "pdf"],
    "css_path": "..."
  }
}


## 2. setup_guide.sh

### Quoi
Script **Bash interactif** qui guide l’utilisateur pas à pas pour configurer le projet  
(création de dossiers, choix de formats, templates, mise à jour du `config.json`).

### Comment
- Utilise des menus clairs, des couleurs, des confirmations *yes/no*.
- Crée des templates vierges ou copie des fichiers existants.
- Appelle `update_config()` pour modifier `config.json`.
- Vérifie la présence des outils et propose des solutions.

### Squelette (structure principale)

```bash
# 1. Vérification des dépendances
# 2. Création des dossiers input/output
# 3. Configuration interactive de chaque section
# 4. Mise à jour du config.json
# 5. Configuration du fichier de sortie et des exports

## 3. main.py

### Quoi
Point d’entrée **Python** qui orchestre la génération complète de la documentation.

### Comment
- Charge le `config.json`.
- Traite chaque section via des fonctions dédiées (`process_section_*`).
- Appelle le `DocumentationBuilder` pour la section *Structure* (XMI).
- Gère les exports (**HTML, PDF, DOCX**).
- Affiche un rapport final clair.

### Squelette (structure principale)

```python
def main():
    args = parse_arguments()
    config = load_config(...)
    # Traitement des sections
    sections = [...]
    generate_documentation(...)
    export_documentation(...)
```

## Pourquoi une vraie IHM avec PySide6 est la bonne décision

### 📊 Comparatif

| Critère                  | Script Bash (`setup_guide_gama.sh`) | Interface PySide6 (GUI) | Gagnant   |
|---------------------------|-------------------------------------|--------------------------|-----------|
| **Ergonomie / Client-friendly** | Moyenne (console, saisie texte) | Excellente (formulaires, file pickers, boutons, prévisualisation) | PySide6 |
| **Feedback utilisateur** | Limité (couleurs + echo)            | Très riche (progress bar, validation en temps réel, messages colorés) | PySide6 |
| **Utilisateurs cibles**  | Développeurs / power users          | Toute l’équipe (ingénieurs, chercheurs, stagiaires) | PySide6 |
| **Maintenance long terme** | Facile mais fragile sur Windows    | Plus propre, testable, extensible | PySide6 |
| **Aspect professionnel** | "Outil interne"                     | "Vrai logiciel"          | PySide6 |
| **Temps de développement** | Très rapide                        | Plus long au départ      | Bash (court terme) |

### ✅ Conclusion
- **PySide6** est le choix gagnant pour la majorité des critères : ergonomie, feedback, accessibilité, maintenance et aspect professionnel.  
- Le **script Bash** reste utile pour un déploiement rapide ou des besoins très techniques à court terme.  
- Pour un projet pérenne et orienté utilisateur, l’IHM PySide6 s’impose comme la meilleure solution.


## Structure globale de l’application
```text
GAMA_Generator/
├── main_gui.py                  ← Point d’entrée principal (fenêtre principale)
├── config_gama.json             ← Configuration persistante (comme avant)
├── ui/
│   ├── main_window.py           ← Fenêtre principale avec onglets ou wizard
│   ├── setup_wizard.py          ← Assistant pas-à-pas (recommandé)
│   └── dialogs/
│       └── output_dialog.py     ← Dialog pour configurer sortie
├── src/                         ← Ton pipeline existant (assembler, generator, etc.)
└── output_gaml/                 ← Dossier de sortie
```

## Un Wizard (assistant pas-à-pas) plutôt qu’une seule grande fenêtre

Un assistant en plusieurs étapes rend la configuration plus claire et intuitive pour l’utilisateur.

### 🟢 Étape 1 : Bienvenue + Vérification des dépendances
- Message de bienvenue
- Bouton **"Vérifier les dépendances Python"**
- Affichage des résultats (✅ vert / ❌ rouge)

### 📂 Étape 2 : Configuration du fichier XMI
- Bouton **"Parcourir"** pour sélectionner le fichier `.xmi`
- Affichage du chemin sélectionné
- Validation (fichier existe + extension correcte)

### 📁 Étape 3 : Dossier des pseudo-codes
- Bouton **"Parcourir"** pour choisir le dossier *input*
- Option **"Créer un dossier par défaut"**

### 📤 Étape 4 : Configuration de la sortie
- Champ **"Dossier de sortie"**
- Champ **"Nom du fichier monolithique"**
- Checkbox **"Mode modulaire"**
- Checkbox **"Générer les réflexes"**
- Checkbox **"Activer les diagnostics détaillés"**

### 🚀 Étape 5 : Résumé + Lancement
- Affichage récapitulatif de tous les choix
- Bouton **"Sauvegarder la configuration"**
- Bouton **"Lancer la génération maintenant"**



