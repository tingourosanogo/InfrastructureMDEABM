# src/parsers/json_parser.py

import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ParserError(Exception):
    pass

def load_json_to_dict(file_path: str) -> Dict[str, Any]:
    """Charge JSON avec logging et validation basique (non vide)."""
    try:
        with open(file_path, mode='r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            if not data:
                raise ParserError("Fichier JSON vide.")
            logger.info(f"JSON parsé avec succès: {file_path}")
            return data
    except FileNotFoundError:
        logger.error(f"Fichier JSON manquant: {file_path}")
        raise ParserError(f"Fichier manquant: {file_path}")
    except Exception as e:
        logger.error(f"Erreur parsing JSON {file_path}: {e}")
        raise ParserError(f"Erreur parsing JSON: {e}") from e