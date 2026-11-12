#!/bin/bash

# Couleurs pour l'interface
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction pour demander une confirmation
ask_yes_no() {
    while true; do
        read -p "$1 (yes/no): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

# Fonction pour vérifier l'installation d'un logiciel
check_software() {
    if command -v $1 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Fonction pour choisir le type de fichier
choose_file_type() {
    local section=$1
    shift
    local types=("$@")
    
    echo -e "\n${BLUE}Type de fichier pour $section:${NC}"
    for i in "${!types[@]}"; do
        echo "$((i+1)). ${types[$i]}"
    done
    
    while true; do
        read -p "Choisissez une option (1-${#types[@]}): " choice
        if [[ $choice -ge 1 && $choice -le ${#types[@]} ]]; then
            selected_type=${types[$((choice-1))]}
            #echo "$selected_type" | tr '[:upper:]' '[:lower:]'
            break
        else
            echo "Option invalide. Veuillez choisir entre 1 et ${#types[@]}"
        fi
    done
    
    echo $selected_type
}

# Fonction pour générer le nom de fichier basé sur le type
get_filename() {
    local section=$1
    local filetype=$2
    
    case $filetype in
        "YAML") echo "${section,,}.yml" ;;
        "JSON") echo "${section,,}.json" ;;
        "CSV") echo "${section,,}.csv" ;;
        "Multi-CSV") echo "${section,,}_data/" ;;
        "XMI") echo "${section,,}.xmi" ;;
        *) echo "${section,,}.txt" ;;
    esac
}

# Fonction pour choisir le délimiteur
choose_delimiter() {
    local section=$1
    
    echo -e "\n${BLUE}Choix du délimiteur pour $section:${NC}"
    echo "1. Virgule [,] (standard)"
    echo "2. Point-virgule [;] (Excel Europe)"
    echo "3. Autre caractère"
    echo "4. Aucun (pour les formats non CSV)"
    
    while true; do
        read -p "Choisissez une option (1-4): " choice
        case $choice in
            1)
                delimiter=","
                break
                ;;
            2)
                delimiter=";"
                break
                ;;
            3)
                read -p "Entrez le caractère délimiteur: " custom_delim
                delimiter="$custom_delim"
                break
                ;;
            4)
                delimiter=""
                break
                ;;
            *)
                echo "Option invalide. Veuillez choisir entre 1 et 4"
                ;;
        esac
    done
    
    echo $delimiter
}

# Fonction pour mettre à jour le config.json
# Fonction pour normaliser le format en minuscules
normalize_format() {
    local format=$1
    echo "$format" | tr '[:upper:]' '[:lower:]'
}

update_config() {
    local section_key=$1
    local filepath=$2
    local format=$3
    local delimiter=$4
    local ignored=$5

     # Normaliser le format en minuscules
    normalized_format=$(normalize_format "$format")
    
    # Conversion pour correspondre à votre structure
    case $section_key in
        "Introduction")
            config_key="Introduction"
            ;;
        "Modele_Conceptuel")
            config_key="Modele_Conceptuel"
            ;;
        "Indicateurs")
            config_key="Indicateurs" 
            ;;
        "Initialisation")
            config_key="Initialisation"
            ;;
        "Mode_Emploi")
            config_key="Mode_Emploi"
            ;;
        *)
            config_key="$section_key"
            ;;
    esac
    
    python3 -c "
# -*- coding: utf-8 -*-
import json
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')


# Charger le config.json existant
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# S'assurer que la section paths existe
if 'paths' not in config:
    config['paths'] = {}

# Échapper les backslashes pour les chemins Windows
input_path_non_escaped = os.path.abspath('$filepath')


# Mettre à jour les chemins avec la structure exacte de votre config
config['paths']['$config_key'] = {
    'input_path': input_path_non_escaped.replace('\\\\', '/'),
    'format': '$normalized_format'
}

# Ajouter json_path si nécessaire (sauf pour XMI)
if '$normalized_format'.lower() in ['multi-csv']:
    # Pour Multi-CSV, le input_path est un dossier
    # On veut créer un JSON dans le même dossier parent
    input_path = '$filepath'
        
    # Nettoyer le chemin du dossier (enlever le slash final si présent)
    if input_path.endswith('/') or input_path.endswith('\\\\'):
        input_path = input_path[:-1]
        
    # Obtenir le nom de base du dossier
    base_name = os.path.basename(input_path)
        
    # Créer le chemin JSON dans le dossier parent
    parent_dir = os.path.dirname(input_path)
    json_filename = base_name + '.json'
    json_path = os.path.join(parent_dir, json_filename)
        
    # Chemin absolu normalisé
    json_path_abs = os.path.abspath(json_path).replace('\\\\', '/')
        
    config['paths']['$config_key']['json_path'] = json_path_abs

    if input_path and os.path.isdir(input_path):
            print(f\"Dossier Multi-CSV: {input_path.replace('\\\\', '/')}\")
            if os.path.exists(input_path):
                files = [f for f in os.listdir(input_path) if f.endswith('.csv')]
                if files:
                    print(\"Fichiers CSV trouvés:\")
                    for file in files:
                        print(f\"  - {file}\")
                else:
                    print(\"Aucun fichier CSV trouvé dans le dossier\")
            
            if json_path and os.path.isfile(json_path):
                print(f\"Fichier de configuration JSON: {json_path.replace('\\\\', '/')}\")
    else:
            print(\"Configuration Multi-CSV non valide\")


elif '$normalized_format'.lower() not in ['xmi']:
    # Pour les autres formats (sauf XMI), créer le chemin JSON correspondant
    if '$filepath'.endswith('.yml'):
        json_path = '$filepath'.replace('.yml', '.json')
    elif '$filepath'.endswith('.yaml'):
        json_path = '$filepath'.replace('.yaml', '.json')
    elif '$filepath'.endswith('.csv'):
        json_path = '$filepath'.replace('.csv', '.json')
    elif '$filepath'.endswith('.json'):
        json_path = '$filepath' 

    # json_filename = os.path.basename('$filepath').split('.')[0] + '.json'
    # json_path = os.path.join(os.path.dirname('$filepath'), json_filename)
    json_path_no_escaped = os.path.abspath(json_path)
    config['paths']['$config_key']['json_path'] = json_path_no_escaped.replace('\\\\', '/')

# Ajouter le délimiteur pour CSV
separator = '$delimiter'
if '$normalized_format'.lower() == 'csv' or '$normalized_format'.lower() == 'multi-csv':
    config['paths']['$config_key']['delimitor'] = separator
else:
    config['paths']['$config_key']['delimitor'] = ''

# Ajouter une note dans le config.json que cette section est ignorée ou non
ignore_value = $ignored
if $ignored:
    # Ajouter un flag pour indiquer que la section est ignorée
    config['paths']['$config_key']['ignored'] = ignore_value
    config['paths']['$config_key']['comment'] = 'Section ignorée lors de la configuration - données manquantes'
else:
    config['paths']['$config_key']['ignored'] = ignore_value

# Sauvegarder la configuration
with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f\"Configuration mise à jour pour  $config_key avec le format $normalized_format\")
"
}  

# Fonction pour obtenir le chemin configuré
get_config_path() {
    local section_key=$1
    
    python3 -c "
import json
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Pour les sections avec sous-structure
    if '$section_key' in config.get('paths', {}):
        print(config['paths']['$section_key'].get('input_path', ''))
    elif '${section_key}_path' in config.get('paths', {}):
        print(config['paths']['${section_key}_path'])
    else:
        print('')
except:
    print('')
"
}


# Fonction pour configurer le fichier de sortie
setup_output_file() {
    print_info "\nConfiguration du fichier de sortie"
    
    # Déterminer le chemin de sortie par défaut
    default_output="output/documentation_$(date +%Y%m%d_%H%M%S).md"
    
    echo "Options pour le fichier de sortie:"
    echo "1. Utiliser le chemin par défaut: $default_output"
    echo "2. Spécifier un chemin personnalisé"
    echo "3. Utiliser le chemin existant dans config.json"
    
    read -p "Choisissez une option (1-3): " output_option
    
    case $output_option in
        1)
            output_path="$default_output"
            ;;
        2)
            read -p "Entrez le chemin complet du fichier de sortie: " custom_output
            output_path="$custom_output"
            ;;
        3)
            # Récupérer le chemin existant s'il existe
            if python3 -c "
import json
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    if 'paths' in config and 'output_path' in config['paths']:
        print(config['paths']['output_path'])
    else:
        print('')
except:
    print('')
" > /tmp/existing_output; then
                existing_output=$(cat /tmp/existing_output)
                if [ -n "$existing_output" ]; then
                    output_path="$existing_output"
                    print_info "Utilisation du chemin existant: $output_path"
                else
                    print_warning "Aucun output_path trouvé dans config.json"
                    output_path="$default_output"
                fi
            fi
            ;;
        *)
            output_path="$default_output"
            ;;
    esac
    
    # Créer le dossier de sortie s'il n'existe pas
    output_dir=$(dirname "$output_path")
    mkdir -p "$output_dir"
    
    # Mettre à jour le config.json
    python3 -c "
# -*- coding: utf-8 -*-
import json
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')


# Charger le config.json existant
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# S'assurer que la section paths existe
if 'paths' not in config:
    config['paths'] = {}

# Échapper les backslashes pour les chemins Windows
output_path_non_escaped = os.path.abspath('$output_path')

# Mettre à jour le output_path avec le chemin absolu
config['paths']['output_path'] = output_path_non_escaped.replace('\\\\', '/')

# Sauvegarder la configuration
with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f\"Output path configuré: {config['paths']['output_path']}\")
"

    print_success "Fichier de sortie configuré: $output_path"
}


# Fonction pour créer un fichier markdown de base
create_default_markdown() {
    local output_file=$1
    
    if [ ! -f "$output_file" ]; then
        cat > "$output_file" << EOF
# Documentation Générée Automatiquement

## Page de Garde
*Document généré le $(date +%Y-%m-%d)*

## Table des Matières
1. [Introduction](#introduction)
2. [Structure du Modèle](#structure-et-dynamique)
3. [Mode d'Emploi](#mode-demploi)
4. [Indicateurs](#indicateurs)
5. [Initialisation](#initialisation)

## Introduction
*Section introduction à compléter*

## Structure du Modèle
*Section structure à compléter*

## Mode d'Emploi
*Section mode d'emploi à compléter*

## Indicateurs
*Section indicateurs à compléter*

## Initialisation
*Section initialisation à compléter*

---
*Document généré avec CIM-PIM Transformation Tool*
EOF
        
        print_success "Fichier markdown de base créé: $output_file"
    else
        print_info "Fichier de sortie existe déjà: $output_file"
    fi
}

# Fonction pour créer des templates
create_template() {
    local section_key=$1
    local section_name=$2
    local selected_type=$3
    local filename=$4
    local delimiter=$5
    local ignored=$6
    
    print_info "Création d'un template $selected_type pour $section_name..."
    
    # Création d'un template selon le type sélectionné
    case $selected_type in
        "YAML")
            cat > "input/$filename" << EOF
# Template YAML pour $section_name
# Format: YAML

metadata:
  title: "Titre de la section"
  description: "Description de la section"
  version: "1.0.0"

content:
  - item: "Exemple"
    description: "Contenu de la section"
    value: 42
EOF
            print_success "Template créé: input/$filename"
            print_success "📝 N'oubliez pas de remplir le template avec vos données!"
            ;;
        "JSON")
            cat > "input/$filename" << EOF
{
  "metadata": {
    "title": "Titre de la section",
    "description": "Description de la section",
    "version": "1.0.0"
  },
  "content": [
    {
      "item": "Exemple",
      "description": "Contenu de la section",
      "value": 42
    }
  ]
}
EOF
            print_success "Template créé: input/$filename"
            print_success "📝 N'oubliez pas de remplir le template avec vos données!"
            ;;
        "CSV")
            # Déterminer le délimiteur approprié
            local delimiter=$delimiter
            
            cat > "input/$filename" << EOF
# Template CSV pour $section_name
# Format: CSV - Délimiteur: '$delimiter'

id${delimiter}name${delimiter}value${delimiter}description
1${delimiter}indicateur_1${delimiter}100${delimiter}"Premier indicateur"
2${delimiter}indicateur_2${delimiter}200${delimiter}"Deuxième indicateur"  
3${delimiter}indicateur_3${delimiter}300${delimiter}"Troisième indicateur"
EOF
            print_success "Template créé: input/$filename"
            print_success "📝 N'oubliez pas de remplir le template avec vos données!"
            ;;
        "Multi-CSV")
            mkdir -p "input/$filename"
            print_info "Création d'un dossier pour les fichiers CSV multiples"

            # Création de quelques fichiers CSV d'exemple
            cat > "input/$filename/parametres.csv" << EOF
# Fichier de paramètres
# Format: CSV - Délimiteur: ','

parametre,valeur,unite,description
temperature,25,°C,"Température ambiante"
humidite,60,%,"Humidité relative"
vitesse_vent,5,km/h,"Vitesse du vent"
EOF
                    
            cat > "input/$filename/initial_values.csv" << EOF
# Valeurs initiales  
# Format: CSV - Délimiteur: ','

id,composant,valeur_initial,min,max
1,biomasse,1000,0,5000
2,population,50,0,200
3,ressources,2000,0,10000
EOF
            print_success "Dossier créé avec des exemples: input/$filename"
            print_success "📝 N'oubliez pas de remplir les templates avec vos données!"
            ;;
        "XMI")
            print_info "Le format XMI nécessite un outil de modélisation"
            print_info "Vous devrez générer ce fichier avec un éditeur dedié"
            print_info "Placez le fichier .xmi dans le dossier input/"
            
            # Créer un fichier d'instructions pour XMI
            cat > "input/README_XMI.md" << EOF
# Instructions pour le fichier XMI

Pour la section $section_name, vous avez besoin d'un fichier XMI.

## Étapes à suivre:

1. Utilisez un éditeur UML comme:
   - GenMyModel (en ligne)
   - Visual Paradigm  
   - Enterprise Architect
   - Draw.io 

2. Créez votre diagramme 

3. Exportez au format XMI 2.1

4. Placez le fichier exporté dans le dossier input/ sous le nom: $filename

5. Relancez le guide de configuration
EOF
            print_info "📋 Instructions créées: input/README_XMI.md"
            ;;
    esac
    
    # Mise à jour de la configuration (sauf pour XMI)
    if [ "$selected_type" != "XMI" ]; then
        update_config "$section_key" "input/$filename" "$selected_type" "$delimiter" "$ignored"
    fi
}

# Fonction pour afficher des exemples de format
show_format_example() {
    local section=$1
    local format=$2
    
    echo -e "\n${BLUE}ℹ️  Exemple de format $format pour $section:${NC}"
    
    case "$format" in
        "YAML")
            case "$section" in
                "Introduction")
                    cat << EOF
# Structure YAML générique pour $section
version: "1.0"
metadata:
  titre: "<Titre du document>"
  auteur: "<Auteur(s) ou équipe>"
  date_creation: "<YYYY-MM-DD>"
  modele_reference: "<Nom ou identifiant du modèle>"

principe_modelisation:
  question_recherche:
    formulation: "<Question de recherche principale>"
    explication: "<Description détaillée de la question et des concepts associés>"
  concepts_fondamentaux:
    entites: "<Description des entités du système>"
    attributs:
      - type: "<Type d'attribut, ex. parametres>"
        definition: "<Définition ou rôle>"
      - type: "<Type d'attribut, ex. variables_etat>"
        definition: "<Définition ou rôle>"
    portee_attributs:
      - "<Portée des attributs, ex. globaux>"
      - "<Portée des attributs, ex. locaux>"
      - "<Portée des attributs, ex. individuels>"
  relation_questions_modele:
    explication: "<Explication des relations entre question et modèle>"
    implication: "<Implications pour l'utilisation du modèle>"

modele_specifique:
  question_centrale:
    formulation: "<Question spécifique du modèle>"
    domaine: "<Domaine d'application>"
    echelle: "<Échelle d'application, ex. territoriale>"
  diagrammes:
    - id: "<Identifiant unique du diagramme>"
      fichier: "<Chemin ou URL du fichier>"
      legende: "<Légende du diagramme>"
      description: "<Description détaillée du diagramme>"
  composants_principaux:
    - nom: "<Nom du composant>"
      description: "<Description du composant>"
      role: "<Rôle ou fonction dans le modèle>"
      types:  # Optionnel, si applicable
        - "<Type ou sous-catégorie>"
      usages:  # Optionnel, si applicable
        - "<Usage ou application>"
  acteurs:
    - type: "<Type d'acteur, ex. individuels>"
      exemple: "<Exemple concret, ex. exploitations>"
    - type: "<Type d'acteur, ex. collectifs>"
      exemple: "<Exemple concret, ex. villages>"

contextualisation:
  domaine_application: "<Domaine(s) d'application>"
  pertinence_scientifique: "<Justification ou pertinence du modèle>"
  public_cible:
    - "<Groupe cible, ex. décideurs politiques>"
    - "<Groupe cible, ex. chercheurs>"

references_bibliographiques:
  - auteur: "<Nom(s) de l'auteur>"
    annee: "<Année de publication>"
    titre: "<Titre de la référence>"
    journal: "<Nom du journal, éditeur ou source>"  # Optionnel
    edition: "<Éditeur, si applicable>"  # Optionnel
EOF
                    ;;
                "Indicateurs")
                    cat << EOF
# Structure YAML générique pour $section
indicators:
  - id: "<Identifiant unique, ex. PA.01.01>"
    name: "<Nom de l'indicateur>"
    category: "<Catégorie, ex. Pastoralisme>"
    source: "<Source ou référence, ex. Auteur et al. (Année), Journal>"
    description: "<Description détaillée de l'indicateur, peut être multi-ligne>"
    formula: "<Formule de calcul, ex. CA = (Nombre UBT) / (Surface pâturable)>"
    unit: "<Unité de mesure, ex. UBT/ha>"
    variables: # Liste des variables utilisées
      - name: "<Nom de la variable, ex. nombre_ubt>"
        entity: "<Entité associée, ex. Troupeau>"
        definition: "<Définition de la variable>"
        unit: "<Unité, ex. UBT>" # Optionnel
    parameters: # Liste des paramètres
      - name: "<Nom du paramètre, ex. facteur_saison>"
        entity: "<Entité associée, ex. Système>"
        definition: "<Définition du paramètre>"
        value: "<Valeur par défaut, ex. 1.2>" # Optionnel
        unit: "<Unité, ex. coefficient>" # Optionnel
EOF
                    ;;
                "Mode_Emploi")
                    cat << EOF
# Structure YAML générique pour $section
version: "<Version du document, ex. 1.2>"
metadata:
  auteur: "<Auteur(s) ou équipe>"
  date_mise_a_jour: "<YYYY-MM-DD>"
  version_modele: "<Nom ou version du modèle, ex. PastoralABM v3.1>"
  reference: "<Référence bibliographique ou source, ex. Nom et al. 2023>"
  licence: "<Type de licence, ex. CC BY-NC 4.0>"

lancement_simulation:
  plateforme_requise:
    os: ["<Systèmes d'exploitation supportés, ex. Windows, Linux, macOS>"]
    memoire_ram: "<Mémoire recommandée/minimum, ex. 16GB/8GB>"
    espace_disque: "<Espace disque requis, ex. 2GB>"
    dependances:
      - "<Nom de la dépendance, ex. GAMA Platform 1.9.1+>"
      - "<Nom de la dépendance, ex. Java 17+>"

  fichiers_necessaires:
    - nom: "<Nom du fichier, ex. main_model.gaml>"
      description: "<Description du fichier>"
      format: "<Format, ex. GAML>"
      exemple: "<Chemin ou exemple, ex. models/.../main_model.gaml>"
    - nom: "<Nom du fichier, ex. config_parameters.xml>"
      description: "<Description du fichier>"
      format: "<Format, ex. XML>"
      parametres_cles: ["<Nom du paramètre, ex. duree_simulation>", "<Nom du paramètre>"]
    - nom: "<Nom du fichier, ex. land_cover.tiff>"
      description: "<Description du fichier>"
      format: "<Format, ex. GeoTIff>"
      resolution: "<Résolution, ex. 10m>" # Optionnel
      systeme_coordonnees: "<Système, ex. WGS84 UTM 28N>" # Optionnel
    - nom: "<Nom du fichier, ex. herd_data.csv>"
      description: "<Description du fichier>"
      format: "<Format, ex. CSV UTF-8>"
      colonnes_obligatoires: ["<Nom de colonne, ex. household_id>", "<Nom de colonne>"]

  procedure:
    - etape: "<Numéro d'étape, ex. 1>"
      commande: "<Commande, ex. gama-headless.exe ...>"
      description: "<Description de l'étape>"
      options: # Optionnel
        - "<Option, ex. --experiment main_experiment>"
      prerequis: "<Prérequis, ex. Environnement graphique>" # Optionnel

entrees:
  interface_utilisateur:
    disponible: <true/false>
    type: "<Nom de l'interface, ex. GAMA Modeling Environment>"
    url: "<URL de l'interface, ex. https://gama-platform.org>" # Optionnel
    fonctionnalites:
      - "<Fonctionnalité, ex. Exploration visuelle des scénarios>"
      - "<Fonctionnalité>"

  fichiers_entree:
    - type: "<Type de données, ex. parametres_globaux>"
      format: "<Format, ex. XML>"
      schema: "<Schéma, ex. schemas/parameters_schema.xsd>" # Optionnel
      description: "<Description du fichier>"
      champs_obligatoires: 
        - "<Champ, ex. simulation_duration: 3650 (10 ans)>"
      couches_requises: # Optionnel, pour données spatiales
        - "<Couche, ex. land_cover: Occupation du sol>"
      variables_cles: # Optionnel, pour données socio-économiques
        - "<Variable, ex. household_size: Taille du ménage>"

sorties:
  visualisation:
    - type: "<Type de visualisation, ex. cartes_dynamiques>"
      format: "<Format, ex. HTML interactif>"
      outils: "<Outils utilisés, ex. GAMA GIS + Leaflet.js>"
      description: "<Description de la visualisation>"
      indicateurs_visuels: # Optionnel
        - "<Indicateur, ex. Densité de troupeaux>"
      indicateurs: # Optionnel
        - "<Indicateur, ex. Biomasse disponible (kg/ha)>"

  fichiers_sortie:
    - type: "<Type de fichier, ex. resultats_bruts>"
      format: "<Format, ex. CSV>"
      colonnes: # Optionnel
        - "<Colonne, ex. step: Pas de temps>"
      indicateurs: # Optionnel
        - "<Indicateur, ex. mean_herd_size: Taille moyenne>"
      description: "<Description du fichier>"
      sections: # Optionnel, pour rapports
        - "<Section, ex. résumé_exécutif>"

  post_traitement:
    outils_recommandes:
      - "<Outil, ex. R Studio (analyse statistique)>"
    scripts_exemples: "<Chemin, ex. scripts/analysis/>" # Optionnel
    methodes_analyse:
      - "<Méthode, ex. ANOVA multi-facteurs>"

EOF
                    ;;
                *)
                    cat << EOF
# Structure YAML générique pour $section
metadata:
  protocol: "<Protocole, ex. ODDv3>"
  model_name: "<Nom du modèle, ex. SocioEco_Model>"
  version: "<Version du modèle, ex. 1.0.0>"
  creation_date: "<YYYY-MM-DD>"
  last_modified: "<YYYY-MM-DD>"
  authors:
    - name: "<Nom de l'auteur, ex. Researcher A>"
      affiliation: "<Institution ou organisation>"
      role: "<Rôle, ex. Domain Expert>"
      orcid: "<ORCID, ex. 0000-0000-0000-0000>" # Optionnel
  references:
    - citation: "<Citation, ex. Grimm et al. (2020) - ODD protocol>"
      doi: "<DOI, ex. 10.18564/jasss.4259>" # Optionnel

global:
  temporal_scope:
    start_date: "<YYYY-MM-DD>"
    end_date: "<YYYY-MM-DD>"
    time_step: "<Durée, ex. 1 day>"
    warmup_period: "<Durée, ex. 365 days>" # Optionnel
  spatial_configuration:
    extent: ["<min_x>", "<min_y>", "<max_x>", "<max_y>"] # Bounding box
    projection: "<Système, ex. EPSG:4326>"
    resolution: "<Résolution, ex. 100 m>" # Optionnel

input_data:
  spatial_data:
    - type: "<Type, ex. raster>"
      format: "<Format, ex. GeoTIFF>"
      path: "<Chemin, ex. data/land_use.tif>"
      description: "<Description, ex. CORINE Land Cover>"
      resolution: "<Résolution, ex. 100m>" # Optionnel
      source: "<Source, ex. EEA>"
      uncertainty: "<Niveau, ex. low>" # Optionnel
      reliability: "<Niveau, ex. high>" # Optionnel
  tabular_data:
    - type: "<Type, ex. csv>"
      path: "<Chemin, ex. data/household_survey.csv>"
      description: "<Description, ex. Socio-economic survey>"
      sample_size: "<Taille, ex. 1500>" # Optionnel
      response_rate: "<Pourcentage, ex. 78%>" # Optionnel
      validation_method: "<Méthode, ex. cross_validation>" # Optionnel

entities:
  - name: "<Nom de l'entité, ex. HouseholdAgent>"
    type: "<Type, ex. agent>"
    count: "<Nombre, ex. 1500>" # Optionnel
    initialization_method: "<Méthode, ex. data_driven>"
    data_source: "<Source, ex. data/household_survey.csv>"
    sampling_strategy: "<Stratégie, ex. stratified_random>" # Optionnel
    stratification_variables: ["<Variable, ex. income_class>", "<Variable>"] # Optionnel
    attribute_mapping: # Optionnel
      - model_attribute: "<Attribut, ex. size_ha>"
        data_field: "<Champ, ex. area>"
        conversion: "<Conversion, ex. square_meters_to_hectares>"

parameters:
  fixed:
    - name: "<Nom, ex. discount_rate>"
      entity: "<Entité, ex. HouseholdAgent>"
      value: "<Valeur, ex. 0.03>"
      unit: "<Unité, ex. dimensionless>"
      definition: "<Définition, ex. Temporal discount rate>"
      source: "<Source, ex. Berger et al. (2007)>"
      uncertainty: # Optionnel
        distribution: "<Distribution, ex. normal>"
        std_dev: "<Écart-type, ex. 0.005>"
      sensitivity_rank: "<Niveau, ex. high>" # Optionnel
      validation: "<Méthode, ex. lab_experiments>" # Optionnel
  variable:
    - name: "<Nom, ex. climate_change_scenario>"
      entity: "<Entité, ex. Global>"
      values: ["<Valeur, ex. RCP2.6>", "<Valeur>"]
      definition: "<Définition, ex. IPCC climate scenarios>"
      source: "<Source, ex. IPCC AR6>"
      impact_assessment: "<Niveau, ex. high>" # Optionnel

state_variables:
  fixed_initialization:
    - name: "<Nom, ex. initial_wealth>"
      entity: "<Entité, ex. HouseholdAgent>"
      value: "<Valeur, ex. 50000>"
      unit: "<Unité, ex. EUR>"
      distribution: "<Distribution, ex. lognormal>"
      parameters:
        "<Paramètre, ex. mean>": "<Valeur, ex. 10.82>"
        "<Paramètre, ex. sigma>": "<Valeur, ex. 0.8>"
      source: "<Source, ex. National statistics>"
  variable_initialization:
    - name: "<Nom, ex. land_use_type>"
      entity: "<Entité, ex. ParcelEntity>"
      values: ["<Valeur, ex. forest>", "<Valeur>"]
      distribution: "<Distribution, ex. categorical>"
      probabilities: ["<Probabilité, ex. 0.3>", "<Probabilité>"]
      source: "<Source, ex. Land cover map>"

scenarios:
  - name: "<Nom, ex. sustainability_transition>"
    description: "<Description, ex. Pathway towards sustainable agroecology>"
    based_on: "<Base, ex. IPCC RCP2.6>" # Optionnel
    parameters:
      "<Paramètre, ex. climate_change_scenario>": "<Valeur, ex. RCP2.6>"
    state_variables:
      "<Variable, ex. initial_investment>": "<Valeur, ex. 20000>"
    validation_status: "<Statut, ex. plausible>" # Optionnel

traceability:
  data_quality:
    - parameter: "<Paramètre, ex. discount_rate>"
      quality_score: "<Score, ex. 0.8>"
      assessment_method: "<Méthode, ex. expert_judgment>"
      experts: # Optionnel
        - name: "<Nom, ex. Dr. Economist>"
          confidence: "<Niveau, ex. high>"
  uncertainty_quantification:
    - parameter: "<Paramètre, ex. soil_mineralization_rate>"
      uncertainty_type: "<Type, ex. epistemic>"
      magnitude: "<Niveau, ex. medium>"
      propagation_method: "<Méthode, ex. monte_carlo>"
  sensitivity_analysis:
    planned_methods: ["<Méthode, ex. SOBOL>", "<Méthode>"]
    parameters_included: "<Portée, ex. all>"
    software: "<Outil, ex. SALib>" # Optionnel

validation:
  methods:
    - name: "<Nom, ex. expert_validation>"
      date: "<YYYY-MM-DD>"
      participants: "<Nombre, ex. 5>" # Optionnel
      result: "<Résultat, ex. parameters_approved>"
    - name: "<Nom, ex. historical_validation>"
      period: "<Période, ex. 2010-2020>"
      metric: "<Métrique, ex. Nash-Sutcliffe>"
      value: "<Valeur, ex. 0.75>"
      threshold: "<Seuil, ex. 0.6>"

initialization_rules:
  - entity: "<Entité, ex. HouseholdAgent>"
    rule: "<Règle, ex. wealth ~ lognormal(10.82, 0.8)>"
    implementation: "<Code, ex. numpy.random.lognormal(10.82, 0.8, n_agents)>"
    assumptions: "<Hypothèses, ex. Wealth distribution follows statistics>" # Optionnel
EOF
                    ;;
            esac
            ;;
            
        "JSON")
            case "$section" in
                "Introduction")
                    cat << EOF
{
  "version": "<Version du document, ex. 1.0>",
  "metadata": {
    "titre": "<Titre du document>",
    "auteur": "<Auteur(s) ou équipe>",
    "date_creation": "<YYYY-MM-DD>",
    "modele_reference": "<Nom ou identifiant du modèle>"
  },
  "principe_modelisation": {
    "question_recherche": {
      "formulation": "<Question de recherche principale>",
      "explication": "<Description détaillée de la question et des concepts associés>"
    },
    "concepts_fondamentaux": {
      "entites": "<Description des entités du système>",
      "attributs": [
        {
          "type": "<Type d'attribut, ex. parametres>",
          "definition": "<Définition ou rôle>"
        },
        {
          "type": "<Type d'attribut, ex. variables_etat>",
          "definition": "<Définition ou rôle>"
        }
      ],
      "portee_attributs": [
        "<Portée des attributs, ex. globaux>",
        "<Portée des attributs, ex. locaux>",
        "<Portée des attributs, ex. individuels>"
      ]
    },
    "relation_questions_modele": {
      "explication": "<Explication des relations entre question et modèle>",
      "implication": "<Implications pour l'utilisation du modèle>"
    }
  },
  "modele_specifique": {
    "question_centrale": {
      "formulation": "<Question spécifique du modèle>",
      "domaine": "<Domaine d'application>",
      "echelle": "<Échelle d'application, ex. territoriale>"
    },
    "diagrammes": [
      {
        "id": "<Identifiant unique du diagramme>",
        "fichier": "<Chemin ou URL du fichier>",
        "legende": "<Légende du diagramme>",
        "description": "<Description détaillée du diagramme>"
      }
    ],
    "composants_principaux": [
      {
        "nom": "<Nom du composant>",
        "description": "<Description du composant>",
        "role": "<Rôle ou fonction dans le modèle>",
        "types": ["<Type ou sous-catégorie>"], // Optionnel
        "usages": ["<Usage ou application>"] // Optionnel
      }
    ],
    "acteurs": [
      {
        "type": "<Type d'acteur, ex. individuels>",
        "exemple": "<Exemple concret, ex. exploitations>"
      }
    ]
  },
  "references_bibliographiques": [
    {
      "auteur": "<Nom(s) de l'auteur>",
      "annee": "<Année de publication>",
      "titre": "<Titre de la référence>",
      "journal": "<Nom du journal, éditeur ou source>", // Optionnel
      "edition": "<Éditeur, si applicable>" // Optionnel
    }
  ]
}
EOF
                    ;;
                "Indicateurs")
                    cat << EOF
{
  "indicators": [
    {
      "id": "<Identifiant unique, ex. PA.01.01>",
      "name": "<Nom de l'indicateur>",
      "category": "<Catégorie, ex. Pastoralisme>",
      "source": "<Source ou référence, ex. Auteur et al. (Année), Journal>",
      "description": "<Description détaillée de l'indicateur>",
      "formula": "<Formule de calcul, ex. CA = (Nombre UBT) / (Surface pâturable)>",
      "unit": "<Unité de mesure, ex. UBT/ha>",
      "variables": [
        {
          "name": "<Nom de la variable, ex. nombre_ubt>",
          "entity": "<Entité associée, ex. Troupeau>",
          "definition": "<Définition de la variable>",
          "unit": "<Unité, ex. UBT>" // Optionnel
        }
      ],
      "parameters": [
        {
          "name": "<Nom du paramètre, ex. facteur_saison>",
          "entity": "<Entité associée, ex. Système>",
          "definition": "<Définition du paramètre>",
          "value": "<Valeur par défaut, ex. 1.2>", // Optionnel
          "unit": "<Unité, ex. coefficient>" // Optionnel
        }
      ]
    }
  ]
}
EOF
                    ;;
                "Mode_Emploi")
                    cat << EOF
{
  "version": "<Version du document, ex. 1.2>",
  "metadata": {
    "auteur": "<Auteur(s) ou équipe>",
    "date_mise_a_jour": "<YYYY-MM-DD>",
    "version_modele": "<Nom ou version du modèle, ex. PastoralABM v3.1>",
    "reference": "<Référence bibliographique, ex. Nom et al. 2023 - Journal>",
    "licence": "<Type de licence, ex. CC BY-NC 4.0>" // Optionnel
  },
  "lancement_simulation": {
    "plateforme_requise": {
      "os": ["<Systèmes d'exploitation, ex. Windows 10/11>"],
      "memoire_ram": "<Mémoire recommandée/minimum, ex. 16GB/8GB>",
      "espace_disque": "<Espace disque requis, ex. 2GB>",
      "dependances": ["<Nom de la dépendance, ex. GAMA Platform 1.9.1+>"]
    },
    "fichiers_necessaires": [
      {
        "nom": "<Nom du fichier, ex. main_model.gaml>",
        "description": "<Description du fichier>",
        "format": "<Format, ex. GAML>",
        "exemple": "<Chemin ou exemple, ex. models/.../main_model.gaml>", // Optionnel
        "parametres_cles": ["<Nom du paramètre, ex. duree_simulation>"], // Optionnel
        "colonnes_obligatoires": ["<Nom de colonne, ex. household_id>"], // Optionnel
        "resolution": "<Résolution, ex. 10m>", // Optionnel
        "systeme_coordonnees": "<Système, ex. WGS84 UTM 28N>" // Optionnel
      }
    ],
    "procedure": [
      {
        "etape": "<Numéro d'étape, ex. 1>",
        "commande": "<Commande, ex. gama-headless.exe ...>",
        "description": "<Description de l'étape>",
        "options": ["<Option, ex. --experiment main_experiment>"], // Optionnel
        "prerequis": "<Prérequis, ex. Environnement graphique>" // Optionnel
      }
    ]
  },
  "entrees": {
    "interface_utilisateur": {
      "disponible": "<true/false>",
      "type": "<Nom de l'interface, ex. GAMA Modeling Environment>",
      "url": "<URL, ex. https://gama-platform.org>", // Optionnel
      "fonctionnalites": ["<Fonctionnalité, ex. Exploration visuelle des scénarios>"]
    },
    "fichiers_entree": [
      {
        "type": "<Type de données, ex. parametres_globaux>",
        "format": "<Format, ex. XML>",
        "schema": "<Schéma, ex. schemas/parameters_schema.xsd>", // Optionnel
        "description": "<Description du fichier>",
        "champs_obligatoires": ["<Champ, ex. simulation_duration: 3650 (10 ans)>"], // Optionnel
        "couches_requises": ["<Couche, ex. land_cover: Occupation du sol>"], // Optionnel
        "variables_cles": ["<Variable, ex. household_size: Taille du ménage>"], // Optionnel
        "systeme_coordonnees": "<Système, ex. WGS84/UTM>" // Optionnel
      }
    ]
  },
  "sorties": {
    "visualisation": [
      {
        "type": "<Type de visualisation, ex. cartes_dynamiques>",
        "format": "<Format, ex. HTML interactif>",
        "outils": "<Outils utilisés, ex. GAMA GIS + Leaflet.js>",
        "description": "<Description de la visualisation>",
        "indicateurs_visuels": ["<Indicateur, ex. Densité de troupeaux>"], // Optionnel
        "indicateurs": ["<Indicateur, ex. Biomasse disponible (kg/ha)>"] // Optionnel
      }
    ],
    "fichiers_sortie": [
      {
        "type": "<Type de fichier, ex. resultats_bruts>",
        "format": "<Format, ex. CSV>",
        "colonnes": ["<Colonne, ex. step: Pas de temps>"], // Optionnel
        "indicateurs": ["<Indicateur, ex. mean_herd_size: Taille moyenne>"], // Optionnel
        "sections": ["<Section, ex. résumé_exécutif>"], // Optionnel
        "description": "<Description du fichier>"
      }
    ],
    "post_traitement": {
      "outils_recommandes": ["<Outil, ex. R Studio (analyse statistique)>"],
      "scripts_exemples": "<Chemin, ex. scripts/analysis/>", // Optionnel
      "methodes_analyse": ["<Méthode, ex. ANOVA multi-facteurs>"] // Optionnel
    }
  }
}
EOF
                    ;;
                *)
                    cat << EOF
{
  "metadata": {
    "protocol": "<Protocole, ex. ODDv3>",
    "model_name": "<Nom du modèle, ex. SocioEco_Model>",
    "version": "<Version du modèle, ex. 1.0.0>",
    "creation_date": "<YYYY-MM-DD>",
    "last_modified": "<YYYY-MM-DD>",
    "authors": [
      {
        "name": "<Nom de l'auteur, ex. Researcher A>",
        "affiliation": "<Institution ou organisation>",
        "role": "<Rôle, ex. Domain Expert>",
        "orcid": "<ORCID, ex. 0000-0000-0000-0000>" // Optionnel
      }
    ],
    "references": [
      {
        "citation": "<Citation, ex. Grimm et al. (2020) - ODD protocol>",
        "doi": "<DOI, ex. 10.18564/jasss.4259>" // Optionnel
      }
    ]
  },
  "global": {
    "temporal_scope": {
      "start_date": "<YYYY-MM-DD>",
      "end_date": "<YYYY-MM-DD>",
      "time_step": "<Durée, ex. 1 day>",
      "warmup_period": "<Durée, ex. 365 days>" // Optionnel
    },
    "spatial_configuration": {
      "extent": ["<min_x>", "<min_y>", "<max_x>", "<max_y>"], // Bounding box
      "projection": "<Système, ex. EPSG:4326>",
      "resolution": "<Résolution, ex. 100 m>" // Optionnel
    }
  },
  "input_data": {
    "spatial_data": [
      {
        "type": "<Type, ex. raster>",
        "format": "<Format, ex. GeoTIFF>",
        "path": "<Chemin, ex. data/land_use.tif>",
        "description": "<Description, ex. CORINE Land Cover>",
        "resolution": "<Résolution, ex. 100m>", // Optionnel
        "source": "<Source, ex. EEA>",
        "uncertainty": "<Niveau, ex. low>", // Optionnel
        "reliability": "<Niveau, ex. high>" // Optionnel
      }
    ],
    "tabular_data": [
      {
        "type": "<Type, ex. csv>",
        "format": "<Format, ex. csv>",
        "path": "<Chemin, ex. data/household_survey.csv>",
        "description": "<Description, ex. Socio-economic survey>",
        "sample_size": "<Taille, ex. 1500>", // Optionnel
        "response_rate": "<Pourcentage, ex. 78%>", // Optionnel
        "validation_method": "<Méthode, ex. cross_validation>" // Optionnel
      }
    ]
  },
  "entities": [
    {
      "name": "<Nom de l'entité, ex. HouseholdAgent>",
      "type": "<Type, ex. agent>",
      "count": "<Nombre, ex. 1500>", // Optionnel
      "initialization_method": "<Méthode, ex. data_driven>",
      "data_source": "<Source, ex. data/household_survey.csv>",
      "sampling_strategy": "<Stratégie, ex. stratified_random>", // Optionnel
      "stratification_variables": ["<Variable, ex. income_class>"], // Optionnel
      "attribute_mapping": [
        {
          "model_attribute": "<Attribut, ex. size_ha>",
          "data_field": "<Champ, ex. area>",
          "conversion": "<Conversion, ex. square_meters_to_hectares>" // Optionnel
        }
      ]
    }
  ],
  "parameters": {
    "fixed": [
      {
        "name": "<Nom, ex. discount_rate>",
        "entity": "<Entité, ex. HouseholdAgent>",
        "value": "<Valeur, ex. 0.03>",
        "unit": "<Unité, ex. dimensionless>",
        "definition": "<Définition, ex. Temporal discount rate>",
        "source": "<Source, ex. Berger et al. (2007)>",
        "uncertainty": {
          "distribution": "<Distribution, ex. normal>", // Optionnel
          "std_dev": "<Écart-type, ex. 0.005>" // Optionnel
        },
        "sensitivity_rank": "<Niveau, ex. high>", // Optionnel
        "validation": "<Méthode, ex. lab_experiments>" // Optionnel
      }
    ],
    "variable": [
      {
        "name": "<Nom, ex. climate_change_scenario>",
        "entity": "<Entité, ex. Global>",
        "values": ["<Valeur, ex. RCP2.6>"],
        "definition": "<Définition, ex. IPCC climate scenarios>",
        "source": "<Source, ex. IPCC AR6>",
        "impact_assessment": "<Niveau, ex. high>" // Optionnel
      }
    ]
  },
  "state_variables": {
    "fixed_initialization": [
      {
        "name": "<Nom, ex. initial_wealth>",
        "entity": "<Entité, ex. HouseholdAgent>",
        "value": "<Valeur, ex. 50000>",
        "unit": "<Unité, ex. EUR>",
        "distribution": "<Distribution, ex. lognormal>",
        "parameters": {
          "<Paramètre, ex. mean>": "<Valeur, ex. 10.82>",
          "<Paramètre, ex. sigma>": "<Valeur, ex. 0.8>"
        },
        "source": "<Source, ex. National statistics>"
      }
    ],
    "variable_initialization": [
      {
        "name": "<Nom, ex. land_use_type>",
        "entity": "<Entité, ex. ParcelEntity>",
        "values": ["<Valeur, ex. forest>"],
        "distribution": "<Distribution, ex. categorical>",
        "probabilities": ["<Probabilité, ex. 0.3>"],
        "source": "<Source, ex. Land cover map>"
      }
    ]
  },
  "scenarios": [
    {
      "name": "<Nom, ex. sustainability_transition>",
      "description": "<Description, ex. Pathway towards sustainable agroecology>",
      "based_on": "<Base, ex. IPCC RCP2.6>", // Optionnel
      "parameters": {
        "<Paramètre, ex. climate_change_scenario>": "<Valeur, ex. RCP2.6>"
      },
      "state_variables": {
        "<Variable, ex. initial_investment>": "<Valeur, ex. 20000>"
      },
      "validation_status": "<Statut, ex. plausible>" // Optionnel
    }
  ],
  "traceability": {
    "data_quality": [
      {
        "parameter": "<Paramètre, ex. discount_rate>",
        "quality_score": "<Score, ex. 0.8>",
        "assessment_method": "<Méthode, ex. expert_judgment>",
        "experts": [
          {
            "name": "<Nom, ex. Dr. Economist>",
            "confidence": "<Niveau, ex. high>"
          }
        ] // Optionnel
      }
    ],
    "uncertainty_quantification": [
      {
        "parameter": "<Paramètre, ex. soil_mineralization_rate>",
        "uncertainty_type": "<Type, ex. epistemic>",
        "magnitude": "<Niveau, ex. medium>",
        "propagation_method": "<Méthode, ex. monte_carlo>"
      }
    ],
    "sensitivity_analysis": {
      "planned_methods": ["<Méthode, ex. SOBOL>"],
      "parameters_included": "<Portée, ex. all>",
      "software": "<Outil, ex. SALib>" // Optionnel
    }
  },
  "validation": {
    "methods": [
      {
        "method_name": "<Nom, ex. expert_validation>",
        "validation_date": "<YYYY-MM-DD>", // Optionnel
        "participants": "<Nombre, ex. 5>", // Optionnel
        "period": "<Période, ex. 2010-2020>", // Optionnel
        "metric": "<Métrique, ex. Nash-Sutcliffe>", // Optionnel
        "metric_value": "<Valeur, ex. 0.75>", // Optionnel
        "threshold": "<Seuil, ex. 0.6>", // Optionnel
        "result": "<Résultat, ex. parameters_approved>" // Optionnel
      }
    ]
  },
  "initialization_rules": [
    {
      "entity": "<Entité, ex. HouseholdAgent>",
      "rule": "<Règle, ex. wealth ~ lognormal(10.82, 0.8)>",
      "implementation": "<Code, ex. numpy.random.lognormal(10.82, 0.8, n_agents)>",
      "assumptions": "<Hypothèses, ex. Wealth distribution follows statistics>" // Optionnel
    }
  ]
}
EOF
                    ;;
            esac
            ;;
            
        "CSV")
            case "$section" in
                "Indicateurs")
                    cat << EOF
```csv
id,name,category,source,description,formula,unit,variables,parameters
"<Identifiant unique, ex. PA.01.01>","<Nom de l'indicateur, ex. Charge animale instantanée>","<Catégorie, ex. Pastoralisme>","<Source ou référence, ex. Auteur et al. (Année), Journal>","<Description détaillée de l'indicateur, peut être multi-ligne>","<Formule de calcul, ex. CA = (Nombre UBT) / (Surface pâturable)>","<Unité de mesure, ex. UBT/ha>","<variable_name>:<entity>:<definition>:<unit>|...","<parameter_name>:<entity>:<definition>:<unit>:<value>|..."
```
EOF
                    ;;
            esac
            ;;
            
        "Multi-CSV")
            echo -e "${GREEN}Structure de dossier Multi-CSV:${NC}"
            echo "input/${section,,}_data/"
            echo "├── global_config.csv"
            echo "├── input_data.csv"
            echo "├── entities.csv"
            echo "├── parameters.csv"
            echo "├── state_variables.csv"
            echo "├── scenarios.csv"
            echo "├── traceability.csv"
            echo "├── validation.csv"
            echo "├── initialization_rules.csv"
            echo ""
            echo "${BLUE}Exemple parameters.csv:${NC}"
            echo "name,value,unit,description"
            echo "temperature,25,°C,Température moyenne"
            echo "humidity,60,%,Humidité relative"
            echo "population,1000,persons,Population initiale"
            ;;
            
        "XMI")
            echo -e "${YELLOW}Le format XMI est généré automatiquement par les outils de modélisation${NC}"
            echo ""
            echo "${GREEN}Outils recommandés:${NC}"
            echo "• GenMyModel (en ligne)"
            echo "• Visual Paradigm (desktop)"  
            echo "• Enterprise Architect (desktop)"
            echo "• Draw.io avec extension UML (gratuit)"
            echo ""
            echo "${BLUE}Le fichier XMI doit contenir:${NC}"
            echo "- Classes avec attributs et opérations"
            echo "- Associations entre classes"
            echo "- Diagrammes"
            echo "- Métadonnées du modèle"
            ;;
    esac
    
    echo -e "\n${YELLOW}📝 Appuyez sur Entrée pour continuer...${NC}"
    read -p ""
}


# Début du guide
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}   GUIDE D'INSTALLATION - GÉNÉRATEUR DOCS      ${NC}"
echo -e "${GREEN}===============================================${NC}\n"

# Étape 1: Vérification des dépendances
echo -e "\n${GREEN}=== ETAPE 1: Vérification des dépendances système ===${NC}\n"

# Vérification Python
if check_software "python3"; then
    print_success "Python 3 est installé"
    python_version=$(python3 --version)
    echo "Version: $python_version"
else
    print_error "Python 3 n'est pas installé"
    if ask_yes_no "Voulez-vous installer Python 3 maintenant?"; then
        print_info "Installation de Python 3..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt update && sudo apt install -y python3 python3-pip
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install python3
        else
            print_error "Système d'exploitation non supporté. Veuillez installer Python manuellement."
            exit 1
        fi
    else
        print_error "Python 3 est requis. Installation manuelle nécessaire."
        exit 1
    fi
fi

# Vérification pip
if check_software "pip3"; then
    print_success "pip3 est installé"
else
    print_info "Installation de pip3..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt install -y python3-pip
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python3 get-pip.py
        rm get-pip.py
    fi
fi

# Installation des dépendances Python
print_info "\nVérification des dépendances Python...\n"

declare -A dependencies=(
    ["lxml"]="libxml2 et libxslt (pour le parsing XMI)"
    ["pyyaml"]="PyYAML (pour les fichiers YAML)"
    ["questionary"]="Questionary (pour les interfaces interactives)"
)

for lib in "${!dependencies[@]}"; do
    if python3 -c "import $lib" 2>/dev/null; then
        print_success "$lib est installé"
    else
        print_warning "$lib n'est pas installé - ${dependencies[$lib]}"
        if ask_yes_no "Voulez-vous installer $lib?"; then
            pip3 install $lib
            if [ $? -eq 0 ]; then
                print_success "$lib installé avec succès"
            else
                print_error "Échec de l'installation de $lib"
                if [[ "$lib" == "lxml" ]]; then
                    print_info "Installation des dépendances système pour lxml..."
                    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                        sudo apt install -y libxml2-dev libxslt-dev python3-dev
                    elif [[ "$OSTYPE" == "darwin"* ]]; then
                        brew install libxml2 libxslt
                        export LDFLAGS="-L/usr/local/opt/libxml2/lib -L/usr/local/opt/libxslt/lib"
                        export CPPFLAGS="-I/usr/local/opt/libxml2/include -I/usr/local/opt/libxslt/include"
                    fi
                    pip3 install lxml
                fi
            fi
        fi
    fi
done


# Fonction pour installer les dépendances d'export
install_export_dependencies() {
    print_info "Installation des dépendances pour l'export HTML/PDF"
    
    # Dépendances Python pour l'export
    export_packages=("markdown==3.4.4" "pdfkit==1.0.0")
    
    for package in "${export_packages[@]}"; do
        if ! python3 -c "import $(echo $package | cut -d'=' -f1)" 2>/dev/null; then
            print_info "Installation de $package..."
            pip3 install $package
            if [ $? -eq 0 ]; then
                print_success "$package installé avec succès"
            else
                print_error "Échec de l'installation de $package"
                return 1
            fi
        else
            print_success "$package est déjà installé"
        fi
    done
    
    # Installation de wkhtmltopdf selon l'OS
    print_info "Installation de wkhtmltopdf pour l'export PDF"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if ! command -v wkhtmltopdf &> /dev/null; then
            print_info "Installation de wkhtmltopdf sur Linux..."
            
            # Ubuntu/Debian
            if command -v apt &> /dev/null; then
                sudo apt update
                sudo apt install -y wkhtmltopdf
                
            # CentOS/RHEL
            elif command -v yum &> /dev/null; then
                sudo yum install -y wkhtmltopdf
                
            # Fedora
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y wkhtmltopdf
                
            else
                print_warning "Gestionnaire de packages non supporté. Installer wkhtmltopdf manuellement:"
                print_info "Visitez https://wkhtmltopdf.org/downloads.html"
                return 1
            fi
            
            if command -v wkhtmltopdf &> /dev/null; then
                print_success "wkhtmltopdf installé avec succès"
            else
                print_error "Échec de l'installation de wkhtmltopdf"
                return 1
            fi
        else
            print_success "wkhtmltopdf est déjà installé"
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v wkhtmltopdf &> /dev/null; then
            print_info "Installation de wkhtmltopdf sur macOS..."
            
            if command -v brew &> /dev/null; then
                brew install --cask wkhtmltopdf
            else
                print_warning "Homebrew non installé. Installer wkhtmltopdf manuellement:"
                print_info "brew install --cask wkhtmltopdf"
                print_info "Ou téléchargez depuis https://wkhtmltopdf.org/downloads.html"
                return 1
            fi
            
            if command -v wkhtmltopdf &> /dev/null; then
                print_success "wkhtmltopdf installé avec succès"
            else
                print_error "Échec de l'installation de wkhtmltopdf"
                return 1
            fi
        else
            print_success "wkhtmltopdf est déjà installé"
        fi
        
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        print_info "Installation de wkhtmltopdf sur Windows..."
        print_warning "wkhtmltopdf nécessite une installation manuelle sur Windows"
        print_info "1. Téléchargez depuis https://wkhtmltopdf.org/downloads.html"
        print_info "2. Installez le programme"
        print_info "3. Ajoutez le chemin d'installation aux variables d'environnement PATH (set PATH=%PATH%;\"C:/Program\ Files/wkhtmltopdf/bin/\")"
        print_info "4. Redémarrez le terminal après l'installation"
        
        if ask_yes_no "Avez-vous déjà installé wkhtmltopdf?"; then
            print_success "wkhtmltopdf configuré"
        else
            print_warning "L'export PDF ne fonctionnera pas sans wkhtmltopdf"
            return 1
        fi
    else
        print_warning "Système d'exploitation non supporté: $OSTYPE"
        print_info "Installation manuelle de wkhtmltopdf requise"
        return 1
    fi
    
    return 0
}

# Étape 2: Configuration de la structure des dossiers
echo -e "\n${GREEN}=== ETAPE 2: Configuration de la structure des dossiers ===${NC}\n"

# Création des dossiers nécessaires
mkdir -p input output exports assets schemas

print_success "Structure de dossiers créée:"
echo "├── input/      # Fichiers d'entrée"
echo "├── output/     # Documentation générée"
echo "├── exports/    # Documentation exportée HTML/PDF"
echo "├── assets/     # Images et ressources"
echo "└── schemas/    # Schémas de validation"



# Fonction pour scanner les assets et les schemas
scan_assets_and_schemas() {
    print_info "Scan des dossiers assets et schemas..."
    
    # Scanner le dossier assets
    if [ -d "assets" ] && [ "$(ls -A assets 2>/dev/null)" ]; then
        print_success "Dossier assets trouvé avec des fichiers"
        
        # Mise à jour du config.json avec les assets
        python3 -c "
import json
import os

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Initialiser la section assets si elle n'existe pas
if 'assets' not in config:
    config['assets'] = {}

# Scanner tous les fichiers dans assets
assets_path = 'assets'
for item in os.listdir(assets_path):
    item_path = os.path.join(assets_path, item)
    if os.path.isfile(item_path):
        file_name = os.path.splitext(item)[0]  # Nom sans extension
        item_non_escape_path = os.path.abspath(item_path)
        config['assets'][file_name] = item_non_escape_path.replace('\\\\', '/')
        print(f\"Asset détecté: {file_name} -> {item_path}\")

with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
    else
        print_info "Dossier assets vide ou inexistant"
    fi
    
    # Scanner le dossier schemas
    if [ -d "schemas" ] && [ "$(ls -A schemas 2>/dev/null)" ]; then
        print_success "Dossier schemas trouvé avec des fichiers"
        
        # Mise à jour du config.json avec les schemas
        python3 -c "
import json
import os

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Initialiser la section schemas si elle n'existe pas
if 'schemas' not in config:
    config['schemas'] = {}

# Scanner tous les fichiers dans schemas
schemas_path = 'schemas'
for item in os.listdir(schemas_path):
    item_path = os.path.join(schemas_path, item)
    if os.path.isfile(item_path):
        file_name = os.path.splitext(item)[0]  # Nom sans extension
        item_non_escape_path = os.path.abspath(item_path)
        config['schemas'][file_name] = item_non_escape_path.replace('\\\\', '/')
        print(f\"Schema détecté: {file_name} -> {item_path}\")

with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
    else
        print_info "Dossier schemas vide ou inexistant"
    fi
}

# Fonction pour configurer les métadonnées
configure_metadata() {
    print_info "\nConfiguration des Métadonnées"
    
    current_title=$(python3 -c "import json; print(json.load(open('config.json')).get('metadata', {}).get('title', ''))" 2>/dev/null || echo "")
    current_version=$(python3 -c "import json; print(json.load(open('config.json')).get('metadata', {}).get('version', '1.0.0'))" 2>/dev/null || echo "1.0.0")
    
    read -p "Titre de la documentation [$current_title]: " title
    title=${title:-$current_title}
    
    read -p "Sous-titre: " subtitle
    read -p "Version [$current_version]: " version
    version=${version:-$current_version}
    
    read -p "Statut (Brouillon/Revue/Final) [Brouillon]: " status
    status=${status:-Final}
    
    read -p "Classification (Interne/Public/Confidentiel) [Interne]: " classification
    classification=${classification:-Interne}
    
    read -p "Langue (fr/en/es) [fr]: " language
    language=${language:-fr}
    
    # NOUVELLE METHODE POUR LES MOTS-CLÉS - Accepte tous caractères
    echo "Mots-clés (séparés par des virgules, tous caractères acceptés): "
    echo "Ex: pastoralisme, modélisation-GAMA, socio-écologique, résilience_climatique"
    read -p "➡️  " keywords_input
    
    # Nettoyage et validation des mots-clés
    keywords_list=()
    IFS=',' read -ra raw_keywords <<< "$keywords_input"
    for keyword in "${raw_keywords[@]}"; do
        # Nettoyer les espaces et garder tous les caractères spéciaux
        cleaned_keyword=$(echo "$keyword" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [ -n "$cleaned_keyword" ]; then
            keywords_list+=("$cleaned_keyword")
        fi
    done
    
    # Conversion en JSON array avec protection des guillemets
    if [ ${#keywords_list[@]} -gt 0 ]; then
        keywords_json="["
        for i in "${!keywords_list[@]}"; do
            # Échapper les guillemets et caractères spéciaux pour JSON
            escaped_keyword=$(printf '%s' "${keywords_list[$i]}" | python3 -c "
import json
import sys
print(json.dumps(sys.stdin.read().strip()))
")
            keywords_json+="$escaped_keyword"
            if [ $i -lt $((${#keywords_list[@]} - 1)) ]; then
                keywords_json+=", "
            fi
        done
        keywords_json+="]"
    else
        keywords_json="[]"
    fi
    
    python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Préparer les mots-clés en toute sécurité
keywords = $keywords_json

config['metadata'] = {
    'title': '$title',
    'subtitle': '$subtitle',
    'version': '$version',
    'date_creation': '$(date +%Y-%m-%d)',
    'date_version': '$(date +%Y-%m-%d)',
    'status': '$status',
    'classification': '$classification',
    'language': '$language',
    'keywords': keywords
}

with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
    
    print_success "Métadonnées sauvegardées avec succès"
    print_info "Mots-clés enregistrés: ${keywords_list[*]}"
}


# Fonction pour configurer les auteurs
configure_authors() {
    print_info "\nConfiguration des Auteurs"
    
    authors=()
    while true; do
        echo "Ajouter un auteur (ou 'stop' pour terminer):"
        read -p "Nom complet: " name
        [ "$name" = "stop" ] && break
        
        read -p "Affiliation: " affiliation
        read -p "Rôle: " role
        read -p "Email: " email
        read -p "ORCID (optionnel): " orcid
        
        authors+=("{\"name\": \"$name\", \"affiliation\": \"$affiliation\", \"role\": \"$role\", \"email\": \"$email\", \"orcid\": \"$orcid\"}")
        
        echo "Auteur ajouté. Ajouter un autre?"
    done
    
    if [ ${#authors[@]} -gt 0 ]; then
        authors_json=$(IFS=,; echo "[${authors[*]}]")
        python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
config['authors'] = json.loads('$authors_json')
with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
    fi
}

# Fonction pour configurer le projet
configure_project() {
    print_info "\nConfiguration du Projet"
    
    read -p "Nom du projet: " project_name
    read -p "Acronyme: " acronym
    read -p "Organisme de financement: " funding
    read -p "Numéro de subvention: " grant_number
    read -p "Durée (ex: 2024-2026): " duration
    read -p "Site web: " website
    read -p "Dépôt de code: " repository
    
    python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

config['project'] = {
    'name': '$project_name',
    'acronym': '$acronym',
    'funding': '$funding',
    'grant_number': '$grant_number',
    'duration': '$duration',
    'website': '$website',
    'repository': '$repository'
}

with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
}

# Fonction pour configurer la documentation
configure_documentation() {
    print_info "\nConfiguration de la Documentation"
    
    read -p "Type de document [Documentation Technique]: " doc_type
    doc_type=${doc_type:-Documentation Technique}
    
    read -p "Objectif: " purpose
    read -p "Public cible: " audience
    read -p "Standard de conformité [ISO/IEC/IEEE 26515]: " conformance
    conformance=${conformance:-ISO/IEC/IEEE 26515}
    
    read -p "Licence [CC BY-NC-SA 4.0]: " license
    license=${license:-CC BY-NC-SA 4.0}
    
    python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

config['documentation'] = {
    'type': '$doc_type',
    'purpose': '$purpose',
    'audience': '$audience',
    'conformance': '$conformance',
    'license': '$license'
}

with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
}

# Fonction pour configurer les infos techniques
configure_technical() {
    print_info "\nConfiguration des Informations Techniques"
    
    read -p "Version du modèle: " model_version
    read -p "Plateforme (ex: GAMA 1.9.2): " platform
    read -p "Langage de programmation: " programming_language
    read -p "RAM minimale: " min_ram
    read -p "RAM recommandée: " rec_ram
    
    echo "Dépendances (séparées par des virgules, tous caractères acceptés): "
    echo " Ex: Java 17, Python 3.10+, GDAL 3.4, Docker-Compose"
    read -p "  " deps_input
    
    echo "Formats de données supportés (séparés par des virgules): "
    echo " Ex: GeoTIFF, GeoJSON, CSV, NetCDF"
    read -p "  " formats_input
    
    # Utiliser Python pour éviter les problèmes de tableaux Bash
    python3 -c "
import json
import sys

def safe_string(value):
    \"\"\"Retourne une chaîne safe ou une chaîne vide\"\"\"
    return value if value is not None else ''

def parse_comma_separated(input_str):
    \"\"\"Parse une chaîne séparée par des virgules en liste\"\"\"
    if not input_str or not input_str.strip():
        return []
    # Split sur les virgules et nettoyer chaque élément
    return [item.strip() for item in input_str.split(',') if item.strip()]

# Charger la config existante
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}
except Exception as e:
    print(f'Erreur lecture config: {e}')
    config = {}

# Traitement sécurisé des entrées
dependencies = parse_comma_separated('''$deps_input''')
data_formats = parse_comma_separated('''$formats_input''')

# Mettre à jour la configuration
config['technical'] = {
    'model_version': safe_string('$model_version'),
    'platform': safe_string('$platform'),
    'programming_language': safe_string('$programming_language'),
    'minimum_ram': safe_string('$min_ram'),
    'recommended_ram': safe_string('$rec_ram'),
    'dependencies': dependencies,
    'data_formats': data_formats
}

# Sauvegarder
try:
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print('Configuration technique sauvegardée avec succès!')
    print(f'Dépendances ({len(dependencies)}): {dependencies}')
    print(f'Formats ({len(data_formats)}): {data_formats}')
except Exception as e:
    print(f'Erreur sauvegarde: {e}')
    sys.exit(1)
"
}

# Fonction pour vérifier si une section est remplie
is_section_complete() {
    local section=$1
    python3 -c "
import json
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    section_data = config.get('$section', {})
    
    if '$section' == 'authors':
        # Pour les auteurs, on vérifie s'il y a au moins un auteur
        print('COMPLETE' if isinstance(section_data, list) and len(section_data) > 0 else 'INCOMPLETE')
    elif isinstance(section_data, dict):
        # Pour les autres sections, on vérifie si non vide
        print('COMPLETE' if section_data else 'INCOMPLETE')
    else:
        print('INCOMPLETE')
except:
    print('INCOMPLETE')
"
}

# Fonction pour afficher le menu dynamique
show_config_menu() {
    completed_sections=()
    
    # Vérifier chaque section
    declare -A sections=(
        ["metadata"]="1. Métadonnées"
        ["authors"]="2. Auteurs" 
        ["project"]="3. Information Projet"
        ["documentation"]="4. Documentation"
        ["technical"]="5. Information Technique"
    )
    
    echo -e "\n${BLUE}=== CONFIGURATION CONFIG.JSON ===${NC}"
    config_element=("metadata" "authors" "project" "documentation" "technical")
    for section in "${config_element[@]}"; do
        if [ "$(is_section_complete $section)" = "COMPLETE" ]; then
            completed_sections+=("$section")
        else
            echo "${sections[$section]}"
        fi
    done
    
    # Options toujours disponibles
    echo "6. Assets et Schemas (automatique)"
    echo "7. Passer à l'étape suivante"
    echo "8. Aperçu du config.json actuel"
    echo "9. Réinitialiser une section"
    
    # Afficher les sections complétées
    if [ ${#completed_sections[@]} -gt 0 ]; then
        echo -e "\n${GREEN}✓ Sections complétées:${NC}"
        for section in "${completed_sections[@]}"; do
            echo "  ✓ ${sections[$section]#*. }"
        done
    fi
}

# Fonction pour réinitialiser une section
reset_section() {
    echo -e "\n${YELLOW}=== RÉINITIALISER UNE SECTION ===${NC}"
    
    # Définir les sections avec leurs numéros
    declare -A sections=(
        ["1"]="metadata:Métadonnées"
        ["2"]="authors:Auteurs" 
        ["3"]="project:Information Projet"
        ["4"]="documentation:Documentation"
        ["5"]="technical:Information Technique"
    )
    
    echo "Quelle section voulez-vous réinitialiser?"
    key_order=("1" "2" "3" "4" "5")
    echo "0 - Annuler"
    for key in "${key_order[@]}"; do
        IFS=':' read -ra section_info <<< "${sections[$key]}"
        echo "$key - ${section_info[1]}"
    done
    
    read -p "Choisissez une option (0-5): " section_choice
    
    if [ "$section_choice" = "0" ]; then
        return
    fi
    
    if [ -n "${sections[$section_choice]}" ]; then
        IFS=':' read -ra section_info <<< "${sections[$section_choice]}"
        section_key="${section_info[0]}"
        section_name="${section_info[1]}"
        
        if ask_yes_no "Êtes-vous sûr de vouloir réinitialiser $section_name?"; then
            python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

if '$section_key' == 'authors':
    config['$section_key'] = []
else:
    config['$section_key'] = {}

with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
            print_success "Section $section_name réinitialisée"
        fi
    else
        print_error "Choix invalide. Veuillez choisir entre 0 et 5."
    fi
}


# Étape 3: Configuration du fichier config.json
echo -e "\n${GREEN}=== ETAPE 3: Configuration du fichier config.json ===${NC}\n"

if [ -f "config.json" ]; then
    print_success "config.json existe déjà"
    if ask_yes_no "Voulez-vous le recréer?"; then
        rm config.json
    else
        print_info "Utilisation du fichier config.json existant"
        config_exists=true
    fi
fi

if [ ! "$config_exists" = true ]; then
    # Création du fichier config.json de base
    cat > config.json << EOF
{
    "metadata": {},
    "authors": [],
    "project": {},
    "documentation": {},
    "technical": {},
    "paths": {
        "output_path": "$(pwd)/output/documentation.md"
    },
    "assets": {},
    "schemas": {}
}
EOF
    print_success "Fichier config.json créé avec les valeurs par défaut"
fi


# Menu de configuration interactif
while true; do
    show_config_menu
    
    read -p "Choisissez une option (1-9): " config_option
    
    case $config_option in
        1)
            if [ "$(is_section_complete metadata)" = "COMPLETE" ]; then
                print_info "Les métadonnées sont déjà complètes. Utilisez l'option 9 pour les modifier."
            else
                configure_metadata
            fi
            ;;
        2)
            if [ "$(is_section_complete authors)" = "COMPLETE" ]; then
                print_info "Les auteurs sont déjà configurés. Utilisez l'option 9 pour les modifier."
            else
                configure_authors
            fi
            ;;
        3)
            if [ "$(is_section_complete project)" = "COMPLETE" ]; then
                print_info "Les informations projet sont déjà complètes. Utilisez l'option 9 pour les modifier."
            else
                configure_project
            fi
            ;;
        4)
            if [ "$(is_section_complete documentation)" = "COMPLETE" ]; then
                print_info "La documentation est déjà configurée. Utilisez l'option 9 pour les modifier."
            else
                configure_documentation
            fi
            ;;
        5)
            if [ "$(is_section_complete technical)" = "COMPLETE" ]; then
                print_info "Les informations techniques sont déjà complètes. Utilisez l'option 9 pour les modifier."
            else
                configure_technical
            fi
            ;;
        6)
            scan_assets_and_schemas
            ;;
        7)
            # Vérifier si les sections obligatoires sont remplies
            incomplete_sections=()
            for section in metadata authors project; do
                if [ "$(is_section_complete $section)" = "INCOMPLETE" ]; then
                    incomplete_sections+=("$section")
                fi
            done
            
            if [ ${#incomplete_sections[@]} -eq 0 ]; then
                break
            else
                print_warning "Sections obligatoires non complétées:"
                for section in "${incomplete_sections[@]}"; do
                    case $section in
                        "metadata") echo "  - Métadonnées" ;;
                        "authors") echo "  - Auteurs" ;;
                        "project") echo "  - Information Projet" ;;
                    esac
                done
                if ! ask_yes_no "Voulez-vous quand même continuer?"; then
                    continue
                else
                    break
                fi
            fi
            ;;
        8)
            echo -e "\n${GREEN}=== APERÇU CONFIG.JSON ===${NC}"
            python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
print(json.dumps(config, indent=2, ensure_ascii=False))
"
            ;;
        9)
            reset_section
            ;;
        *)
            print_error "Option invalide"
            ;;
    esac
done

# SCANNER LES ASSETS ET SCHEMAS EXISTANTS
print_info "Scan des assets et schemas existants..."
scan_assets_and_schemas


# Étape 4: Configuration des fichiers d'entrée avec guide détaillé
echo -e "\n${GREEN}=== ETAPE 4: Configuration des fichiers d'entrée pour chaque section ===${NC}\n"
echo "Nous allons maintenant configurer chaque section de la documentation."
echo "Pour chaque section, vous pourrez choisir le format de fichier et fournir les données."
echo -e "-----------------------------------------------------------------------------\n"

declare -A section_types=(
    ["Introduction"]="YAML JSON"
    ["Modele_Conceptuel"]="XMI"
    ["Initialisation"]="YAML Multi-CSV JSON"
    ["Indicateurs"]="YAML CSV JSON" 
    ["Mode_Emploi"]="YAML JSON"
)

declare -A section_descriptions=(
    ["Introduction"]="Présentation générale du modèle et de ses objectifs"
    ["Modele_Conceptuel"]="Modèle conceptuel au format XMI"
    ["Initialisation"]="Données initiales et paramètres de démarrage"
    ["Indicateurs"]="Indicateurs à voir avec le modèle"
    ["Mode_Emploi"]="Instructions d'utilisation et procédures"
)

section_order=("Introduction" "Modele_Conceptuel" "Initialisation" "Indicateurs" "Mode_Emploi")
for section_key in "${section_order[@]}"; do
    # Conversion du nom de section pour l'affichage
    section_name=$(echo "$section_key" | tr '_' ' ')

    ignore=False
    
    echo -e "${GREEN}=== SECTION: $section_name ===${NC}"
    echo -e "${BLUE}Description:${NC} ${section_descriptions[$section_key]}"
    echo ""
    
    # Extraction des types disponibles
    IFS=' ' read -ra types <<< "${section_types[$section_key]}"
    
    # Affichage détaillé des options
    echo "📁 Formats de fichiers disponibles:"
    for i in "${!types[@]}"; do
        case "${types[$i]}" in
            "YAML") echo "   $((i+1)). YAML (.yml) - Format structuré facile à lire" ;;
            "JSON") echo "   $((i+1)). JSON (.json) - Format standard pour les données" ;;
            "CSV") echo "   $((i+1)). CSV (.csv) - Tableur, idéal pour les données tabulaires" ;;
            "Multi-CSV") echo "   $((i+1)). Multi-CSV (dossier/) - Multiple fichiers CSV pour données complexes" ;;
            "XMI") echo "   $((i+1)). XMI (.xmi) - Format standard pour les modèles" ;;
        esac
    done
    echo ""
    
    # Choix du type de fichier avec guide
    while true; do
        read -p "🎯 Choisissez le format pour '$section_name' (1-${#types[@]}): " choice
        
        if [[ $choice -ge 1 && $choice -le ${#types[@]} ]]; then
            selected_type=${types[$((choice-1))]}
            echo -e "${GREEN}✓ Format sélectionné: $selected_type${NC}"
            break
        else
            print_error "Option invalide. Veuillez choisir un nombre entre 1 et ${#types[@]}"
        fi
    done

    # Choix du délimiteur si format CSV
    delimiter=""
    if [[ "$selected_type" == "CSV" || "$selected_type" == "Multi-CSV" ]]; then
        echo -e "\n${BLUE}Choix du délimiteur pour $section:${NC}"
        echo "1. Virgule [,] (standard)"
        echo "2. Point-virgule [;] (Excel Europe)"
        echo "3. Tabulation"
        echo "4. Autre caractère"
        
        while true; do
            read -p "Choisissez une option (1-4): " choice
            case $choice in
                1)
                    delimiter=","
                    break
                    ;;
                2)
                    delimiter=";"
                    break
                    ;;
                3)
                    delimiter="\\t"
                    break
                    ;;
                4)
                    read -p "Entrez le caractère délimiteur: " custom_delim
                    delimiter="$custom_delim"
                    break
                    ;;
                *)
                    echo "Option invalide. Veuillez choisir entre 1 et 4"
                    ;;
            esac
        done
    else
        # Pour les formats non CSV, délimiteur vide
        delimiter=''
    fi
    
    # Génération du nom de fichier
    filename=$(get_filename "$section_key" "$selected_type")



    print_info "Type sélectionné: $selected_type"
    if [ -n "$delimiter" ]; then
        print_info "Délimiteur sélectionné: '$delimiter'"
    fi
    
    echo -e "\n📂 Fichier attendu:${NC} input/$filename"
    
    # Vérification si le fichier existe déjà
    if [ -f "input/$filename" ] || [ -d "input/$filename" ]; then
        echo -e "${GREEN}✓ Fichier/dossier existant trouvé: input/$filename${NC}"
        if ask_yes_no "Voulez-vous utiliser le fichier existant?"; then
            # Mise à jour de la configuration
            update_config "$section_key" "input/$filename" "$selected_type" "$delimiter" "$ignore"
            echo -e "${GREEN}✓ Configuration mise à jour"
            echo -e "-----------------------------------------\n"
            continue
        fi
    fi
    
    # Options détaillées
    echo -e "\n${BLUE}Options disponibles:${NC}"
    echo "1. 📂 Utiliser un fichier existant (copier dans input/)"
    echo "2. 🆕 Créer un template vierge (je vais le remplir après)"
    echo "3. ⏭️  Ignorer cette section pour le moment"
    echo "4. ℹ️  Voir un exemple de format"
    
    while true; do
        read -p "🎯 Que voulez-vous faire? (1-4): " option
        
        case $option in
            1)
                echo -e "\n📂 Utilisation d'un fichier existant"
                read -p "Entrez le chemin complet vers votre fichier: " filepath
                
                if [ -f "$filepath" ] || [ -d "$filepath" ]; then
                    if [ -d "$filepath" ] && [ "$selected_type" = "Multi-CSV" ]; then
                        mkdir -p "input/$filename"
                        cp -r "$filepath"/* "input/$filename/"
                        echo -e "${GREEN}✓ Dossier copié avec succès vers input/$filename"
                    else
                        cp "$filepath" "input/$filename"
                        echo -e "${GREEN}✓ Fichier copié avec succès vers input/$filename"
                    fi
                    update_config "$section_key" "input/$filename" "$selected_type" "$delimiter" "$ignore"
                else
                    print_error "Fichier/dossier non trouvé: $filepath"
                    echo "Veuillez vérifier le chemin et réessayer."
                fi
                break
                ;;
            2)
                echo -e "\n🆕 Création d'un template vierge"
                ignore=True
                create_template "$section_key" "$section_name" "$selected_type" "$filename" "$delimiter" "$ignore"
                update_config "$section_key" "input/$filename" "$selected_type" "$delimiter" "$ignore"
                break
                ;;
            3)
                echo -e "\n⏭️ Section '$section_name' ignorée"
                # MAINTENANT ON AJOUTE QUAND MÊME LES CHEMINS PAR DÉFAUT
                ignore=True
                update_config "$section_key" "input/$filename" "$selected_type" "$delimiter" "$ignore"

                echo "Vous pourrez la configurer plus tard en éditant directement config.json"
                break
                ;;
            4)
                show_format_example "$section_name" "$selected_type"
                ;;
            *)
                print_error "Option invalide. Veuillez choisir entre 1 et 4."
                ;;
        esac
    done
    echo -e "-----------------------------------------\n"
done

# Configuration du fichier de sortie
echo -e "${GREEN}=== Configuration du fichier de sortie Markdown ===${NC}"

setup_output_file

# Créer le fichier markdown de base
if [ -n "$output_path" ]; then
    create_default_markdown "$output_path"
fi



# Etape 5: Vérification finale adaptée
echo -e "\n${GREEN}=== ETAPE 5: Vérification finale ===${NC}\n"

echo "Récapitulatif de la configuration:"
echo -e "${GREEN}✓ Dépenda+nces système vérifiées"
echo -e "${GREEN}✓ Structure de dossiers créée"
echo -e "${GREEN}✓ Fichier config.json configuré"

print_info "\nFichiers d'entrée détectés:"
for item in input/*; do
    if [ -f "$item" ] || [ -d "$item" ]; then
        echo -e "${GREEN}✓${NC} $item"
        if [ -d "$item" ]; then
            for subitem in "$item"/*; do
                if [ -f "$subitem" ]; then
                    echo "  ├── $(basename "$subitem")"
                fi
            done
        fi
    fi
done

# Afficher les types sélectionnés
print_info "\nTypes de fichiers configurés:"
python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
for key in config['paths']:
    if key.endswith('_format'):
        section = key.replace('_format', '').replace('_', ' ').title()
        print(f\"{section}: {config['paths'][key].upper()}\")
"

# Afficher le chemin de sortie configuré
output_path_from_config=$(python3 -c "
import json
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(config.get('paths', {}).get('output_path', 'Non configuré'))
except:
    print('Erreur de lecture')
")

echo -e "${GREEN}✓${NC} Fichier de sortie: $output_path_from_config"


# Fonction pour configurer l'export dans config.json
configure_export_settings() {
    local formats=$1
    local css_path=$2
    
    print_info "Configuration des paramètres d'export dans config.json..."
    
    python3 -c "
import json
import os

# Charger la configuration existante
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Préparer la configuration d'export
export_config = {
    'formats': $formats,
    'css_path': '$css_path' if '$css_path' and os.path.exists('$css_path') else None,
    'output_dir': 'exports'
}

# Ajouter la section export
config['export'] = export_config

# Sauvegarder la configuration mise à jour
with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print('Configuration d\'export sauvegardée dans config.json')
"
}

# Fonction pour obtenir les préférences d'export
get_export_preferences() {
    print_info "Configuration des préférences d'export"
    
    # Choix du format d'export
    echo -e "\n${BLUE}Formats d'export disponibles:${NC}"
    echo "1. HTML seulement"
    echo "2. PDF seulement"
    echo "3. HTML et PDF"
    echo "4. Aucun export"
    
    while true; do
        read -p "Choisissez une option (1-4): " export_option
        
        case $export_option in
            1)
                formats="['html']"
                break
                ;;
            2)
                formats="['pdf']"
                break
                ;;
            3)
                formats="['html', 'pdf']"
                break
                ;;
            4)
                formats="[]"
                break
                ;;
            *)
                echo "Option invalide. Veuillez choisir 1-4"
                ;;
        esac
    done
    
    # Si aucun export, on sort
    if [ "$formats" = "[]" ]; then
        configure_export_settings "[]" ""
        return 0
    fi
    
    # Demande de CSS pour l'export HTML
    css_path=""
    if [[ "$formats" == *"html"* ]]; then
        if ask_yes_no "Voulez-vous utiliser un fichier CSS personnalisé?"; then
            read -p "Chemin vers le fichier CSS: " custom_css
            if [ -f "$custom_css" ]; then
                css_path="$custom_css"
                print_success "Fichier CSS trouvé: $css_path"
            else
                print_warning "Fichier CSS non trouvé: $custom_css"
                if ask_yes_no "Créer un template CSS?"; then
                    mkdir -p assets
                    css_path="assets/custom.css"
                    cat > "$css_path" << EOF
/* Style personnalisé pour la documentation */
body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 20px;
    color: #333;
    max-width: 1000px;
    margin: 0 auto;
    background-color: #fafafa;
}

.header {
    text-align: center;
    margin-bottom: 2em;
    padding: 2em;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h1, h2, h3, h4, h5, h6 {
    color: #2c3e50;
    margin-top: 1.5em;
}

h1 {
    border-bottom: 3px solid #3498db;
    padding-bottom: 0.3em;
}

h2 {
    border-bottom: 2px solid #ecf0f1;
    padding-bottom: 0.2em;
}

code {
    background-color: #f8f9fa;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', monospace;
    color: #e74c3c;
}

pre {
    background-color: #2d3748;
    color: #e2e8f0;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
    border-left: 4px solid #4299e1;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    box-shadow: 0 2px 3px rgba(0, 0, 0, 0.1);
}

th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

th {
    background-color: #3498db;
    color: white;
    font-weight: bold;
}

.footer {
    text-align: center;
    margin-top: 3em;
    padding: 1em;
    border-top: 1px solid #ecf0f1;
    color: #7f8c8d;
    font-size: 0.9em;
}
EOF
                    print_success "Template CSS créé: $css_path"
                else
                    print_info "Utilisation du CSS par défaut"
                fi
            fi
        fi
    fi
    
    # Sauvegarder la configuration d'export
    configure_export_settings "$formats" "$css_path"
    
    # Installation des dépendances si nécessaire
    if [ "$formats" != "[]" ]; then
        if ask_yes_no "Voulez-vous installer les dépendances d'export maintenant?"; then
            install_export_dependencies
        else
            print_info "Les dépendances d'export pourront être installées plus tard"
            print_info "Pour installer manuellement: pip install markdown pdfkit"
        fi
    fi
    
    return 0
}



# Etape 6: Génération de la documentation
echo -e "\n${GREEN}=== ETAPE 6: Génération de la documentation ===${NC}\n"


# Configuration des préférences d'export
if ask_yes_no "Voulez-vous configurer les exports (HTML/PDF) maintenant?"; then
    get_export_preferences
else
    # Ajouter une section export vide si elle n'existe pas
    python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
if 'export' not in config:
    export_config = {
        'formats': [],
        'css_path': None,
        'output_dir': 'exports'
    }

    # Ajouter la section export
    config['export'] = export_config
    
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
"
    print_info "Vous pourrez configurer les exports plus tard dans config.json"
fi

if ask_yes_no "Voulez-vous générer la documentation maintenant?"; then
    # Vérifier que le output_path est configuré
    if [ -z "$output_path_from_config" ] || [ "$output_path_from_config" = "Non configuré" ]; then
        print_warning "Output path non configuré, utilisation de la valeur par défaut"
        output_path="output/documentation.md"
        python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
config['paths']['output_path'] = '$(pwd)/$output_path'
with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
    fi
    
    print_info "Lancement de la génération..."
    
    if [ -f "main.py" ]; then
        python3 main.py
        if [ $? -eq 0 ]; then
            print_success "Documentation générée avec succès!"
            # Vérifier que le fichier a été créé
            final_output=$(python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
print(config.get('paths', {}).get('output_path', ''))
")
            
            if [ -f "$final_output" ]; then
                print_info "Fichier de sortie: $final_output"
                print_info "Taille du fichier: $(du -h "$final_output" | cut -f1)"

                # Vérifier si l'export automatique a été configuré
                export_config=$(python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
export_formats = config.get('export', {}).get('formats', [])
if export_formats:
    print('export_configured')
    print(','.join(export_formats))
")

                if [[ "$export_config" == *"export_configured"* ]]; then
                    # Extraire les formats d'export
                    formats_line=$(echo "$export_config" | grep -v "export_configured")
                    IFS=',' read -ra export_formats <<< "$formats_line"
                    
                    if [ ${#export_formats[@]} -gt 0 ]; then
                        print_success "✅ Export automatique configuré pour: ${export_formats[*]}"
                    fi
                fi
                
                # Affichage d'un aperçu
                if ask_yes_no "Voulez-vous voir un aperçu de la documentation?"; then
                    echo -e "\n${BLUE}=== APERÇU DE LA DOCUMENTATION ===${NC}"
                    head -n 15 "$final_output"
                    echo -e "${BLUE}===================================${NC}"
                fi
            else
                print_error "Le fichier de sortie n'a pas été créé: $final_output"
            fi
        else
            print_error "Erreur lors de la génération"
            print_info "Vérifiez les logs pour plus d'informations"
        fi
    else
        print_error "Fichier main.py non trouvé"
        print_info "Assurez-vous d'être dans le bon répertoire"
    fi
else
    print_info "Vous pouvez générer la documentation plus tard avec:"
    echo "python3 main.py"
fi

# Etape 7: Instructions finales
echo -e "\n${GREEN}=== ETAPE 7: Instructions finales ===${NC}\n"


echo -e "$🎉 Installation terminée !"
echo ""

# Afficher la configuration d'export
export_config=$(python3 -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
export_settings = config.get('export', {})
formats = export_settings.get('formats', [])
css_path = export_settings.get('css_path', 'Aucun')

if formats:
    print('Configuration d\\'export:')
    print(f'   Formats: {formats}')
    print(f'   CSS: {css_path}')
else:
    print('Aucun export configuré')
")

echo "$export_config"
echo ""

echo "Prochaines étapes:"
echo "1. Modifiez les fichiers dans input/ pour votre contenu spécifique"
echo "2. Ajustez config.json selon vos besoins"
echo "3. Régénérez la documentation: python3 main.py"
echo ""
echo "Commandes d'export disponibles:"
echo "  python3 main.py --export html       # Export HTML"
echo "  python3 main.py --export pdf        # Export PDF"
echo "  python3 main.py --export html pdf   # Export HTML et PDF"
echo "  python3 main.py --export html --css assets/custom.css  # Avec CSS personnalisé"
echo ""
echo "Fichier de sortie configuré:"
echo -e "➡️  $output_path_from_config${NC}"
echo ""
echo "Structure recommandée:"
echo "input/"
echo "├── introduction.yml          # Section introduction"
echo "├── Modele_Conceptuel.xmi     # Modèle conceptuel (XMI)"
echo "├── indicators.yml            # Indicateurs et métriques"
echo "├── initialization_data       # Données d'initialisation"
echo "└── user_manual.yml           # Mode d'emploi"
echo ""
echo "output/"
echo "└── documentation.md          # Documentation générée"
echo ""
echo "exports/"
echo "├── documentation.html        # Version HTML"
echo "└── documentation.pdf         # Version PDF"

echo -e "\n${GREEN}==============================================="
echo -e "${GREEN}        GUIDE TERMINÉ AVEC SUCCÈS !            "
echo -e "${GREEN}==============================================="