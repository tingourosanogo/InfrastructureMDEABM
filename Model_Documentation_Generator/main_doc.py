#!/usr/bin/env python3
# main.py
import logging
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import shutil

# Configure le path Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.sections.coverPage import CoverPageSection
from src.sections.introduction import IntroductionSection
from src.sections.indicators import IndicatorsSection
from src.sections.initialization import InitializationSection
from src.sections.userManual import UserManualSection
from src.loader.introduction_loader import IntroductionLoader
from src.loader.indicator_loader import IndicatorLoader
from src.loader.initialization_loader import InitializationLoader
from src.loader.userManual_loader import UserManual_Loader
from src.parsers.uml_parser import UMLParser
from src.parsers.dsl_parser import DSLParser
from src.doc_builder import DocumentationBuilder
from src.exporter.exporters import DocumentationExporter, check_export_dependencies


# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(
        description="CIM-PIM Transformation Tool - Générateur de Documentation Technique",
        epilog="Exemples d'utilisation:\n"
               "  python main.py\n"
               "  python main.py --config config_documentation.json --output docs.md\n"
               "  python main.py --sections Introduction Structure --export html pdf\n"
               "  python main.py --verbose --debug --export html --css style.css",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Arguments principaux
    parser.add_argument(
        '--config', 
        default='config_documentation.json',
        help='Fichier de configuration (défaut: config_documentation.json)'
    )
    
    parser.add_argument(
        '--output', 
        help='Fichier de sortie Markdown (défaut: valeur de config_documentation.json)'
    )
    
    # Sections spécifiques
    parser.add_argument(
        '--sections',
        nargs='+', 
        choices=['Introduction', 'Structure', 'Indicateurs', 'Initialisation', 'Mode d\'emploi'],
        help='Sections spécifiques à générer (csv: Introduction,Structure,Indicateurs,Initialisation,Mode d\'emploi)'
    )
    
    # Options d'export
    parser.add_argument(
        '--export', 
        nargs='+', 
        choices=['html', 'pdf', 'docx'],
        help='Formats d\'export supplémentaires'
    )
    
    parser.add_argument(
        '--export-dir', 
        help='Dossier d\'export (défaut: exports)'
    )
    
    parser.add_argument(
        '--css',
        help='Feuille de style CSS personnalisée pour les exports'
    )
    
    # Options de debug
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Mode verbeux avec plus d\'informations'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Mode debug avec logs détaillés'
    )
    
    # Options de traitement
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Forcer la régénération même si les fichiers existent'
    )
    
    parser.add_argument(
        '--validate', 
        action='store_true',
        help='Valider les fichiers d\'entrée avant génération'
    )
    
    # Options spécifiques XMI
    parser.add_argument(
        '--xmi-path',
        help='Chemin alternatif vers le fichier XMI (écrase config_documentation.json)'
    )
    
    return parser.parse_args()

def validate_config(config: Dict[str, Any]) -> bool:
    """Valide la configuration"""
    required_paths = ['paths']
    if not all(key in config for key in required_paths):
        logging.error("Configuration invalide: sections manquantes")
        return False
    return True


def load_config(config_path: str) -> dict:
    """Charge la configuration globale"""
    try:
        with open(config_path, mode='r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur chargement config : {str(e)}")
        raise

def should_skip_section(section_config: Dict) -> bool:
    """Détermine si une section doit être sautée"""
    return section_config.get('ignored', False)

def check_section_file(section_name: str, section_config: Dict) -> bool:
    """Vérifie si le fichier d'une section existe et n'est pas ignoré"""
    if should_skip_section(section_config):
        logger.warning(f"Section {section_name} ignorée (config: ignored=true)")
        return False
    
    input_path = section_config.get('input_path')
    if not input_path:
        logger.warning(f"Section {section_name} : aucun fichier fourni")
        return False
    
    if not os.path.exists(input_path):
        logger.warning(f"Section {section_name} : fichier introuvable {input_path}")
        return False
    
    return True

def generate_documentation(output_path: Path, sections: List[str]) -> None:
    """Génère le document final combiné""" 
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n\n".join(sections), encoding="utf-8")
        logger.info(f"DOCUMENTATION GENERE : {output_path}")
    except Exception as e:
        logger.error(f"ERREUR GENERATION docs : {str(e)}")
        raise

def export_documentation(output_path: Path, export_opt, css) -> None:
    """Génère le document final combiné""" 
    try:
        exporter = DocumentationExporter()
        export_base = output_path.replace('.md', '')
        
        results = exporter.batch_export(
            export_base, 
            export_opt, 
            css
        )
        
        for format, success in results.items():
            if success:
                logging.info(f"Export {format.upper()} OK: {export_base}.{format}")
                print(f"Export {format.upper()}: {export_base}.{format}")
            else:
                logging.warning(f"Export {format.upper()} NON REUSSI")
    except Exception as e:
        logger.error(f"ERREUR GENERATION docs : {str(e)}")
        raise

def process_section_introduction(paths: Dict) -> Optional[str]:
    """Traite la section Introduction"""
    section_config = paths.get('Introduction', {})
    
    if not check_section_file('Introduction', section_config):
        return None
    
    try:
        # this temporary file is used to store the processed data from the input file (e.g., CSV, Excel) and is read back for generating the section content. It is not intended to be a permanent output file.
        # create or overwrite a temporary JSON file in temp folder
        temp_dir = Path("temporary_data")
        temp_dir.mkdir(exist_ok=True)
        introductionJson_path = temp_dir / "introduction_data.json"
        
        introduction_format = section_config['format']
        
        introduction_loader = IntroductionLoader()
        introduction_data = introduction_loader.load_introduction_data(
            input_path=Path(section_config['input_path']),
            output_path=introductionJson_path,
            input_format=introduction_format
        )
        
        with open(introductionJson_path, mode='r', encoding='utf-8') as f:
            introduction_data = json.load(f)
        
        return IntroductionSection(introduction_data).generate()
        
    except Exception as e:
        logger.error(f"Erreur section Introduction : {str(e)}")
        return None

def process_section_indicators(paths: Dict) -> Optional[str]:
    """Traite la section Indicateurs"""
    section_config = paths.get('Indicateurs', {})
    
    if not check_section_file('Indicateurs', section_config):
        return None
    
    try:
        temp_dir = Path("temporary_data")
        temp_dir.mkdir(exist_ok=True)
        indicatorsJson_path = temp_dir / "indicators_data.json"

        indicators_format = section_config['format']
        delimitor = section_config.get('delimitor', ';')
        
        indicator_loader = IndicatorLoader()
        indicators_data = indicator_loader.load_indicator_data(
            input_path=Path(section_config['input_path']),
            output_path=indicatorsJson_path,
            input_format=indicators_format,
            delimitor=delimitor
        )
        
        with open(indicatorsJson_path, mode='r', encoding='utf-8') as f:
            indicators_data = json.load(f)
        
        return IndicatorsSection(indicators_data).generate()
        
    except Exception as e:
        logger.error(f"Erreur section Indicateurs : {str(e)}")
        return None

def process_section_initialization(paths: Dict) -> Optional[str]:
    """Traite la section Initialisation"""
    section_config = paths.get('Initialisation', {})
    
    if not check_section_file('Initialisation', section_config):
        return None
    
    try:
        temp_dir = Path("temporary_data")
        temp_dir.mkdir(exist_ok=True)
        initializationJson_path = temp_dir / "initialization_data.json"
        
        initialization_format = section_config['format']
        separator = section_config.get('delimitor', ',')
        
        initialization_loader = InitializationLoader()
        initialization_data = initialization_loader.load_initialization_data(
            input_path=Path(section_config['input_path']),
            output_path=initializationJson_path,
            input_format=initialization_format,
            delimitor=separator
        )
        
        with open(initializationJson_path, mode='r', encoding='utf-8') as f:
            initialization_data = json.load(f)
        
        return InitializationSection(initialization_data).generate()
        
    except Exception as e:
        logger.error(f"Erreur section Initialisation : {str(e)}")
        return None

def process_section_user_manual(paths: Dict) -> Optional[str]:
    """Traite la section Mode d'Emploi"""
    section_config = paths.get('Mode_Emploi', {})
    
    if not check_section_file('Mode_Emploi', section_config):
        return None
    
    try:
        temp_dir = Path("temporary_data")
        temp_dir.mkdir(exist_ok=True)
        userManualJson_path = temp_dir / "userManual_data.json"

        userManual_format = section_config['format']
        
        userManual_loader = UserManual_Loader()
        userManual_data = userManual_loader.load_userManual_data(
            input_path=Path(section_config['input_path']),
            output_path=userManualJson_path,
            input_format=userManual_format
        )
        
        with open(userManualJson_path, mode='r', encoding='utf-8') as f:
            userManual_data = json.load(f)
        
        return UserManualSection(userManual_data).generate()
        
    except Exception as e:
        logger.error(f"Erreur section Mode d'Emploi : {str(e)}")
        return None

def process_section_structure(paths: Dict, config: Dict) -> Optional[str]:
    """Traite la section Structure"""
    section_config = paths.get('Modele_Conceptuel', {})
    
    if not check_section_file('Structure', section_config):
        return None
    
    try:
        xmi_parser = DSLParser(Path(section_config['input_path']))
        builder = DocumentationBuilder(config)
        return builder.build(xmi_parser)
        
    except Exception as e:
        logger.error(f"Erreur section Structure : {str(e)}")
        return None
    

def main():
    try:
        
        args = parse_arguments()
        logging.info(f"Arguments: {vars(args)}")

        # 1. Chargement configuration
        config = load_config(args.config)
        if not validate_config(config):
            sys.exit(1)
        logger.info("DEBUT DE LA GENERATION DE DOCUMENTATION")

        paths = config.get('paths', {})
        
        # 2. Génération des sections
        sections = []
        
        # Page de garde (toujours généré)
        cover_page = CoverPageSection(config).generate()
        if cover_page:
            sections.append(cover_page)
            logger.info("Page de garde - OK")
        else:
            logger.warning("Page de garde - Pas OK ")
        
        # Sections avec traitement individuel
        section_processors = [
            ("Introduction", process_section_introduction),
            ("Structure", lambda p: process_section_structure(p, config)), # lambda pour passer config
            ("Indicateurs", process_section_indicators),
            ("Initialisation", process_section_initialization),
            ("Mode d'Emploi", process_section_user_manual)
        ]

        sections_arg=args.sections
        
        if sections_arg:
            for key, processor in section_processors:
                for section_name in sections_arg:
                    if section_name == key:
                        section_content = processor(paths)
                        if section_content:
                            sections.append(section_content)
                            logger.info(f"Section {section_name} - OK")
                        else:
                            logger.warning(f"Section {section_name} - Pas OK")
        else:
            for section_name, processor in section_processors:
                section_content = processor(paths)
                if section_content:
                    sections.append(section_content)
                    logger.info(f"Section {section_name} - OK")
                else:
                    logger.warning(f"Section {section_name} - Pas OK")
        
        # 3. Production du document final
        
        if args.output:
            output_path=args.output  
        else:
            output_path = Path(paths.get('output_path', 'output/documentation.md'))
        
        output_path_obj = Path(output_path)
        generate_documentation(output_path_obj, sections)

        # 4 Exports supplémentaires
        # Export dans d'autres formats si demandé
        if args.export:
            logging.info(f"Export dans les formats: {args.export}")
        elif 'export' in config and config['export'].get('formats'):
            logging.info(f"Export dans les formats: {config['export']['formats']}")

        
        try:
            # Vérifier les dépendances disponibles
            available_deps = check_export_dependencies()
            
            # Déterminer les formats d'export
            if args.export:
                export_formats = [
                    fmt for fmt in args.export
                    if available_deps.get(fmt, False)
                ]  # Liste depuis CLI
            elif 'export' in config and config['export'].get('formats'):
                export_formats = [
                    fmt for fmt in config['export'].get('formats') 
                    if available_deps.get(fmt, False)
                ]  # Liste depuis config
            else:
                export_formats = []

             
            if not export_formats:
                Formats_demandee = args.export or config['export']['formats']
                logging.warning("Dépendances d'export manquantes. Formats demandés: %s", 
                            Formats_demandee)
                print("Dépendances manquantes pour l'export:")
                if 'pdf' in Formats_demandee and not available_deps['pdf']:
                    print("   PDF: pip install pdfkit")
                if 'docx' in Formats_demandee and not available_deps['docx']:
                    print("   DOCX: pip install python-docx")
            else:
                exporter = DocumentationExporter()
                # Déterminer le CSS
                css_path = None
                if args.css:
                    css_path = args.css
                elif 'export' in config and config['export'].get('css_path'):
                    css_path = config['export']['css_path']
            
                # Déterminer le dossier d'export 
                export_dir = getattr(args, 'export_dir', None)  # Correction: args.export_dir pas args.export-dir
                if not export_dir:
                    if 'export' in config and config['export'].get('output_dir') :
                        export_dir = config['export']['output_dir']
                    else:
                        export_dir = 'exports'
            
                # Création du dossier d'export
                os.makedirs(export_dir, exist_ok=True)
            
                # Chemin de base pour les exports
                base_name = os.path.splitext(os.path.basename(output_path))[0]
                export_base = os.path.join(export_dir, base_name)
            
                # lire le contenu de documentation.md généré
                with open(output_path_obj, "r", encoding="utf-8") as f:
                    markdown_content = f.read()

                results = exporter.batch_export(
                    markdown_content,  
                    export_base, 
                    export_formats, 
                    css_path
                )

                # Nettoyage automatique du dossier temporary_data
                if os.path.exists("temporary_data"):
                    shutil.rmtree("temporary_data")
            
                # Affichage des résultats
                for format, success in results.items():
                    if success:
                        logging.info(f"Export {format.upper()} OK: {export_base}.{format}")
                        print(f"Export {format.upper()}: {export_base}.{format}")
                    else:
                        logging.warning(f"Export {format.upper()} ECHOUE")

        except ImportError:
            logging.warning("Module d'export non disponible. Installer: pip install markdown pdfkit") 
            print("Modules d'export non installés. Exécutez: pip install markdown pdfkit")

        except Exception as e:
            logging.error(f"Erreur lors de l'export: {e}", exc_info=True)
            print(f"Erreur lors de l'export: {e}")
            
        # 4. Rapport final
        logger.info("=" * 50)
        logger.info("RAPPORT DE GENERATION")
        logger.info("=" * 50)
        logger.info(f"Fichier de sortie : {output_path}")
        logger.info(f"Sections OK : {len(sections)}")
        logger.info("PROCESSUS TERMINE AVEC SUCCES !")
        
    except Exception as e:
        logger.critical(f"Echec critique du processus : {str(e)}")
        import traceback
        logger.debug(f"Stack trace: {traceback.format_exc()}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())