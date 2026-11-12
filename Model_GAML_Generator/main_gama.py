#!/usr/bin/env python3
# main_gama.py
import os
import sys
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Configuration du chemin du projet
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))  # Assure que les imports fonctionnent même si le script est lancé depuis un autre répertoire

from src.model_intermediate.assembler import ModelAssembler
from src.gaml_generator.generator import GamlGenerator

# Configuration du logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        #logging.FileHandler(f"generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

# logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

def load_config() -> dict:
    """Charge le fichier de configuration"""
    config_path = Path("config_gama.json")
    if not config_path.exists():
        logger.error("Fichier config_gama.json introuvable.")
        logger.error("   Veuillez exécuter ./setup_guide_gama.sh d'abord.")
        sys.exit(1)
    
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur de lecture du config : {e}")
        sys.exit(1)

def validate_input_files(xmi_path: str, input_dir: str) -> bool:
    """Valide l'existence des fichiers d'entrée nécessaires"""
    logger.info("Validation des fichiers d'entrée...")
    
    xmi_file = Path(xmi_path)
    input_path = Path(input_dir)
    
    issues = []
    
    # Vérification XMI
    if not xmi_file.exists():
        issues.append(f" Fichier XMI manquant: {xmi_path}")
    else:
        logger.info(f"Fichier XMI trouvé: {xmi_file} ({xmi_file.stat().st_size} bytes)")
    
    # Vérification répertoire input
    if not input_path.exists():
        issues.append(f" Répertoire input manquant: {input_dir}")
    else:
        logger.info(f"Répertoire input trouvé: {input_path}")
        
        # Vérification des fichiers attendus
        expected_files = [
            'introduction.yml', 'introduction.yaml', 'introduction.json',
            'user_manual.yml', 'user_manual.yaml', 'user_manual.json', 
            'indicators.csv', 'indicators.yml', 'indicators.yaml', 'indicators.json',
            'initialization.yml', 'initialization.yaml', 'initialization.json'
        ]
        
        found_files = []
        for file_pattern in expected_files:
            matches = list(input_path.glob(file_pattern))
            if matches:
                found_files.append(file_pattern)
                logger.info(f"  {file_pattern} -> {matches[0]}")
        
        if not found_files:
            issues.append(" Aucun fichier de configuration trouvé dans input/")
        else:
            logger.info(f"{len(found_files)} fichiers de configuration détectés")
    
    # Affichage des problèmes
    if issues:
        logger.error("Problèmes de configuration détectés:")
        for issue in issues:
            logger.error(f"  {issue}")
        return False
    
    logger.info("Tous les fichiers d'entrée sont valides")
    return True

def run_generation_pipeline(xmi_path: str, input_dir: str) -> bool:
    """Exécute le pipeline complet de génération avec diagnostic"""
    
    logger.info(" Démarrage du pipeline de génération GAML")
    logger.info(f"XMI: {xmi_path}")
    logger.info(f"Input: {input_dir}")
    
    try:
        # === PHASE I - ASSEMBLAGE ===
        logger.info("Phase I - Assemblage du modèle intermédiaire...")
        assembler = ModelAssembler(xmi_path, input_dir)
        model = assembler.assemble()
        
        # Diagnostic du modèle assemblé
        logger.info("Diagnostic du modèle assemblé:")
        logger.info(f"  • Agents: {len(model.agents)}")
        logger.info(f"  • Propriétés: {len(model.properties)}")
        logger.info(f"  • Processus: {len(model.processes)}")
        logger.info(f"  • Indicateurs: {len(model.indicators)}")
        logger.info(f"  • Paramètres globaux: {len(model.global_parameters)}")
        
        for agent_id, agent in model.agents.items():           
            # Calculer le nombre de processus globaux liés à cet agent
            processes_count = len([
                process for process in model.processes.values() 
                if agent.id in process.subjects_refs # Utilise l'ID de l'agent pour le filtrage
            ])
            # Mise à jour de la ligne de diagnostic
            logger.info(f"  • Agent '{agent.name}': {len(agent.attributes)} attributs, {processes_count} processus liés, count={agent.initial_count}")

        # === PHASE II - GÉNÉRATION ===
        logger.info("Phase II - Génération GAML...")
        
        
        # CHOISIR UN SEUL MODE :
        use_modular = False  # ou True selon votre préférence

        if use_modular:
            # MODE MODULAIRE SEULEMENT
            logger.info("Mode modulaire sélectionné")
            generator = GamlGenerator(model, modular=True)
            main_file = generator.generate()  # Génère model.gaml + fichiers modules
            logger.info(f"Structure modulaire générée: {main_file}")
        else:
            # MODE MONOLITHIQUE SEULEMENT  
            logger.info("Mode monolithique sélectionné")
            generator = GamlGenerator(model, modular=False)
            gaml_file = generator.generate("model_monolithic.gaml")  # Génère UNIQUEMENT ce fichier
            logger.info(f"Fichier monolithique généré: {gaml_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"ERREUR: {e}")
        return False

def main():
    logger.info("=" * 80)
    logger.info("GÉNÉRATEUR DE CODE GAML - Lancement via configuration")
    logger.info("=" * 80)

    config = load_config()

    xmi_path = config["paths"]["xmi"]["directory"]
    input_dir = config["paths"]["input_pseudocode"]["directory"]
    output_path = config["paths"]["output_gaml"]["directory"]
    mode = config["generation"].get("mode", "monolithic")
    diagnostics = config["generation"].get("include_diagnostics", True)

    logger.info(f"XMI              : {xmi_path}")
    logger.info(f"Dossier pseudo   : {input_dir}")
    logger.info(f"Sortie GAML      : {output_path} ({mode})")
    logger.info(f"Diagnostics      : {'Activés' if diagnostics else 'Désactivés'}")

    try:
        # Phase 1 : Assemblage du modèle intermédiaire
        logger.info("\nPhase 1 - Assemblage du modèle intermédiaire...")
        assembler = ModelAssembler(xmi_path, input_dir)
        model = assembler.assemble()


        logger.info(f"Modèle assemblé : {len(model.agents)} agents, "
                    f"{len(model.processes)} processus, "
                    f"{len(model.properties)} propriétés")

        # Phase 2 : Génération GAML
        logger.info(f"Phase 2 - Génération GAML en mode {mode}...")
        generator = GamlGenerator(model, output_dir = output_path, modular=(mode == "modular"))
        
        result_file = generator.generate(output_dir = output_path)

        logger.info(f"\nGÉNÉRATION TERMINÉE AVEC SUCCÈS !")
        logger.info(f"Fichier généré : {result_file}")
        
        if diagnostics:
            logger.info("Pour voir les diagnostics détaillés, activez le mode debug dans le config.")

        
    except Exception as e:
        logger.error(f"Erreur lors de la génération : {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()