import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime
import argparse

# Configuration du chemin du projet
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
sys.path.insert(0, str(project_root))

from src.model_intermediate.assembler import ModelAssembler
from src.gaml_generator.generator import GamlGenerator

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Test du générateur GAML")
    parser.add_argument("--xmi", default="input/modeleElevage_en.xmi", help="Chemin vers le fichier XMI")
    parser.add_argument("--input-dir", default="input", help="Répertoire des fichiers de configuration")
    parser.add_argument("--clean-output", action="store_true", help="Nettoyer le dossier output avant test")
    return parser.parse_args()

def validate_input_files(xmi_path: str, input_dir: str) -> bool:
    logger.info("🔍 Validation des fichiers d'entrée...")
    
    xmi_file = Path(xmi_path)
    input_path = Path(input_dir)
    
    issues = []
    
    if not xmi_file.exists():
        issues.append(f"❌ Fichier XMI manquant: {xmi_path}")
    else:
        logger.info(f"✅ Fichier XMI trouvé: {xmi_file} ({xmi_file.stat().st_size} bytes)")
    
    if not input_path.exists():
        issues.append(f"❌ Répertoire input manquant: {input_dir}")
    else:
        logger.info(f"✅ Répertoire input trouvé: {input_path}")
        
        expected_patterns = [
            'introduction.*', 'user_manual.*', 'indicators.*', 'initialization.*'
        ]
        found = []
        for pattern in expected_patterns:
            matches = list(input_path.glob(pattern))
            if matches:
                found.append(pattern)
                logger.info(f"  📁 {pattern} → {matches[0]}")
        
        if not found:
            issues.append("❌ Aucun fichier de configuration détecté dans input/")
        else:
            logger.info(f"✅ {len(found)} fichiers de configuration détectés")
    
    if issues:
        logger.error("Problèmes de configuration détectés:")
        for issue in issues:
            logger.error(f"  {issue}")
        return False
    
    logger.info("✅ Tous les fichiers d'entrée sont valides")
    return True

def clean_output_directory(output_dir: str):
    output_path = Path(output_dir)
    if output_path.exists():
        logger.info(f"🧹 Nettoyage du dossier output: {output_path}")
        for item in output_path.rglob("*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                item.rmdir()
        output_path.rmdir()
        logger.info("Dossier output nettoyé")
    else:
        logger.info("Aucun dossier output à nettoyer")

def run_generation_pipeline(xmi_path: str, input_dir: str, clean_output: bool = False) -> bool:
    logger.info("🚀 Démarrage du pipeline de génération GAML")
    logger.info(f"XMI: {xmi_path}")
    logger.info(f"Input: {input_dir}")

    if clean_output:
        clean_output_directory("output_gaml")

    try:
        # Phase I - Assemblage
        logger.info("🔄 Phase I - Assemblage du modèle intermédiaire...")
        assembler = ModelAssembler(xmi_path, input_dir)
        model = assembler.assemble()
        
        logger.info("📊 Diagnostic du modèle assemblé:")
        logger.info(f"  • Agents: {len(model.agents)}")
        logger.info(f"  • Propriétés: {len(model.properties)}")
        logger.info(f"  • Processus: {len(model.processes)}")
        logger.info(f"  • Indicateurs: {len(model.indicators)}")
        logger.info(f"  • Paramètres globaux: {len(model.global_parameters)}")

        # Phase II - Génération
        logger.info("🔄 Phase II - Génération GAML...")
        
        # Test mode monolithique
        logger.info("🧪 Test mode monolithique...")
        generator_mono = GamlGenerator(model, modular=False)
        
        success, errors = generator_mono.validate_generation()
        if not success:
            logger.error("❌ Échec validation pré-génération:")
            for error in errors:
                logger.error(f"  • {error}")
            return False
        
        gaml_file = generator_mono.generate("model_monolithic.gaml")
        logger.info(f"✅ Fichier GAML monolithique généré: {gaml_file}")

        report = generator_mono.get_generation_report()
        logger.info("📈 Rapport de génération:")
        for key, value in report.items():
            logger.info(f"  • {key}: {value}")

        # Test mode modulaire
        logger.info("🧪 Test mode modulaire...")
        generator_mod = GamlGenerator(model, modular=True)
        generated_files = generator_mod.generate()
        #logger.info(f"✅ Structure modulaire générée: {len(generated_files)} fichiers")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur critique lors de la génération: {e}")
        logger.debug(traceback.format_exc())
        return False

def main():
    args = parse_args()
    
    logger.info("=" * 60)
    logger.info("🧪 TEST DU GÉNÉRATEUR GAML - DIAGNOSTIC COMPLET")
    logger.info("=" * 60)
    
    if not validate_input_files(args.xmi, args.input_dir):
        logger.error("❌ Arrêt du programme - Fichiers d'entrée invalides")
        sys.exit(1)
    
    success = run_generation_pipeline(args.xmi, args.input_dir, args.clean_output)
    
    if success:
        logger.info("🎉 GÉNÉRATION RÉUSSIE!")
        logger.info("📁 Fichiers générés dans: output_gaml/")
        logger.info("📄 Logs détaillés dans: generation_YYYYMMDD_HHMMSS.log")
    else:
        logger.error("💥 GÉNÉRATION ÉCHOUÉE - Voir les logs pour détails")
        sys.exit(1)

if __name__ == "__main__":
    main()