# src/parsers/yaml_parser.py

import yaml
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ParserError(Exception):
    pass

def load_yaml_to_dict(file_path: str) -> Dict:
    """Charge YAML avec logging et validation basique."""
    try:
        with open(file_path, mode='r', encoding='utf-8') as yaml_file:
            data = yaml.safe_load(yaml_file)
            if not data:
                raise ParserError("Fichier YAML vide.")
            logger.info(f"YAML parsé avec succès: {file_path}")
            return data
    except FileNotFoundError:
        logger.error(f"Fichier YAML manquant: {file_path}")
        raise ParserError(f"Fichier manquant: {file_path}")
    except Exception as e:
        logger.error(f"Erreur parsing YAML {file_path}: {e}")
        raise ParserError(f"Erreur parsing YAML: {e}") from e