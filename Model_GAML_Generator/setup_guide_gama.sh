#!/bin/bash
# setup_guide_gama.sh - Guide interactif pour le générateur de code GAML

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
PURPLE='\033[0;35m'
NC='\033[0m'


print_step() { echo -e "${PURPLE}${BOLD}STEP $1:${NC} $2"; }
print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# Fonctions d'affichage stylisées
print_header() {
    clear
    echo -e "${BLUE}${BOLD}======================================================"
    echo -e "       ⚙️  GAMA SETUP GUIDE - GÉNÉRATEUR GAML"
    echo -e "======================================================${NC}\n"
}

# Fonction pour poser une question oui/non
ask_yes_no() {
    while true; do
        read -p "$1 (yes/no): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Merci de saisir yes ou no.";;
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

# Fonction pour mettre à jour les chemins dans la configuration JSON
update_path_config() {
    local section=$1
    local key=$2
    local default_value=$3
    local new_value=$4

    python3 -c "
import json
import os
import re

path = 'config_gama.json'

section = os.environ.get('section', '$section')
key = os.environ.get('key', '$key')
new_value = os.environ.get('new_value', '$new_value')
default_value = os.environ.get('default_value', '$default_value')
directory = 'directory' 

with open(path, 'r', encoding='utf-8') as f:
    config = json.load(f)

if section not in config:
    config[section] = {}

# on garde le chemin par défaut si la nouvelle valeur est vide (ex: réinitialisation)
if new_value == default_value:
    existing_value = config[section][key][directory]
    new_value = existing_value if existing_value else default_value

# Normalise le chemin et supprime tout préfixe "C:/c/" ou "c:/c/"
abs_path = os.path.abspath(new_value).replace('\\\\', '/')


config['paths'][key] = {
    directory: abs_path,
    'format': config['paths'].get(key, {}).get('format', 'auto')
}

with open('config_gama.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f'{key} mis à jour → {abs_path}')
" 2>/dev/null
}


# Fonction de saisie avec validation de chemin
ask_path() {
    local prompt=$1
    local default=$2
    local user_input
    local abs_input

    while true; do
        # -r prevents backslashes from being interpreted
        read -p "$prompt [$default]: " user_input

        # 1. User pressed Enter (empty input)
        if [ -z "$user_input" ]; then
            if ask_yes_no "Voulez-vous utiliser le chemin par défaut ?"; then
                echo "$default"
                return 0
            else
                continue
            fi
        fi

        # 2. Normalize and check path
        abs_input=$(realpath "$user_input" 2>/dev/null || echo "$user_input")

        # Ensure forward slashes for GAML compatibility
        #user_input_norm="${abs_input//\\//}" # remplace les antislashs par des slashs
        user_input_norm=$(python3 -c "import os; print(os.path.abspath('$abs_input').replace('\\\\', '/'))")

        # 2. Check existence or Create if it's an output
        if [ -e "$user_input_norm" ]; then
            echo "$user_input_norm"
            return 0
        else
            if ! ask_yes_no "Le chemin saisi n'existe pas. Voulez-vous saisir un nouveau chemin?"; then
                echo "$default"
                return 0
            else
                continue
            fi
        fi

     
    done
}

# Fonction pour mettre à jour la configuration dans le fichier JSON
update_value_config() {
    local section=$1
    local key=$2
    local value=$3
    python3 -c "
import json
with open('config_gama.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
if '$section' not in config:
    config['$section'] = {}
config['$section']['$key'] = '$value'

with open('config_gama.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
print('Configuration mise à jour \n')
"  2>/dev/null
}


# ====================== DÉBUT DU GUIDE ======================
clear
print_header

# Étape 1: VERIFICATION ET INSTALLATION DES DEPENDANCES SYSTEME
echo -e "\n${GREEN}=== Vérification des dépendances système ===${NC}\n"

if ask_yes_no "Souhaitez-vous vérifier les dépendances système maintenant?"; then
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
        ["lark"]="Lark (pour le parsing des pseudo-codes)"
        ["jinja2"]="Jinja2 (pour les templates de génération de code)"
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
fi


# Étape 2: CREATION DU FICHIER DE CONFIGURATION SI NECESSAIRE

echo -e "\n${GREEN}=== Configuration du projet GAML ===${NC}\n"

if [ ! -f "config_gama.json" ]; then
    cat > config_gama.json << 'EOF'
{
  "metadata": { "title": "Générateur GAML", "version": "1.0.0" },
  "paths": {
    "xmi": { "directory": "", "format": "xmi" },
    "input_pseudocode": { "directory": "", "format": "auto" },
    "output_gaml": { "directory": "", "modular_dir": "output_gaml/species" }
  },
  "generation": {
    "mode": "monolithic",
    "generate_reflex": true,
    "reflex_suffix": "_dynamics",
    "include_diagnostics": true,
    "minify": false
  }
}
EOF
    print_success "Initialisation du fichier de configuration avec les valeurs par défaut."

else
    print_info "Le fichier de configuration existe déjà. Vous pouvez le modifier manuellement ou continuer pour le reconfigurer."
    # Ecrase des chemins d'entrée/sortie pour forcer la reconfiguration
    #update_path_config "paths" "xmi" "" ""
    #update_path_config "paths" "input_pseudocode" "" ""
    #update_path_config "paths" "output_gaml" "" ""
fi

# Étape 3: FORMULAIRE CLI DE CONFIGURATION
print_step() {
    echo -e "\n${BLUE}=== ÉTAPE $1/4 : $2 ===${NC}\n"
}

print_step "1" "Configuration du fichier XMI"
xmi_existing_path=$(python3 -c "import json; c=json.load(open('config_gama.json')); print(c['paths']['xmi']['directory'])" 2>/dev/null || echo "input/modeleElevage_en.xmi")
xmi_path=$(ask_path "📄 Chemin du fichier XMI" "input/modeleElevage_en.xmi")
update_path_config "paths" "xmi" "input/modeleElevage_en.xmi" "$xmi_path"

print_step "2" "Configuration du dossier des pseudo-codes"
input_existing_path=$(python3 -c "import json; c=json.load(open('config_gama.json')); print(c['paths']['input_pseudocode']['directory'])" 2>/dev/null || echo "input")
input_dir=$(ask_path "📂 Dossier contenant les pseudo-codes" "input")
update_path_config "paths" "input_pseudocode" "input" "$input_dir"

print_step "3" "Configuration du dossier de sortie GAML"
output_existing_path=$(python3 -c "import json; c=json.load(open('config_gama.json')); print(c['paths']['output_gaml']['directory'])" 2>/dev/null || echo "output_gaml")
output_dir=$(ask_path "📁 Dossier de sortie GAML" "output_gaml" "output_dir")

# Création automatique du dossier de sortie
#mkdir -p "$output_dir"
#print_success "Dossier de sortie créé/utilisé : $output_dir"

update_path_config "paths" "output_gaml" "output_gaml" "$output_dir"

# 4. Mode de génération
print_step "4" "Configuration du mode de génération"
echo -e "${BOLD}Mode de structure :${NC}"
echo "  1) Monolithique (Un seul fichier .gaml)"
echo "  2) Modulaire    (Plusieurs fichiers par espèce)"
read -p "Choisissez (1 ou 2) [1]: " mode_choice
if [ "$mode_choice" = "2" ]; then
    update_value_config "generation" "mode" "modular"
    print_info "Mode modulaire activé"
else
    update_value_config "generation" "mode" "monolithic"
    print_info "Mode monolithique activé"
fi

# 5. Options avancées
ask_yes_no "Générer les reflexes automatiquement ?" && reflex=true || reflex=false
update_value_config "generation" "generate_reflex" "$reflex"

ask_yes_no "Activer les diagnostics détaillés ?" && diag=true || diag=false
update_value_config "generation" "include_diagnostics" "$diag"


# Étape 4: LANCEMENT DE LA GÉNÉRATION
#print_header
echo -e "\n${GREEN}=== Configuration terminée ! =========== ${NC}  \n"
xmi_path=$(python3 -c "import json; config=json.load(open('config_gama.json')); print(config['paths']['xmi']['directory'])")
input_dir=$(python3 -c "import json; config=json.load(open('config_gama.json')); print(config['paths']['input_pseudocode']['directory'])")
output_file=$(python3 -c "import json; config=json.load(open('config_gama.json')); print(config['paths']['output_gaml']['directory'])")
mode_choice=$(python3 -c "import json; config=json.load(open('config_gama.json')); print(config['generation']['mode'])")
echo -e "📄 Source XMI :   ${YELLOW}$xmi_path${NC}"
echo -e "📁 Extensions:   ${YELLOW}$input_dir${NC}"
echo -e "🎯 SortieGAML:  ${YELLOW}$output_file${NC}"
echo -e "🏗️  Structure:    ${YELLOW}$mode_choice${NC}"
echo -e "-----------------------------------\n"


if ask_yes_no "Souhaitez-vous lancer la génération maintenant ?"; then
    print_info "Exécution du moteur main_gama.py..."
    python3 main_gama.py && print_success "Génération réussie !" || print_error "Échec de la génération. Veuillez vérifier les messages d'erreur."
fi
    

echo -e "\nPour lancer la génération plus tard avec: ${GREEN}python3 main_gama.py${NC}"
echo -e "Pour reconfigurer : ${GREEN}./setup_guide_gama.sh${NC}"