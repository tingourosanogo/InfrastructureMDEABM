# src/loaders/generic_yaml_json_loader.py

from typing import Dict, Any, List
from pathlib import Path
import logging
from ..parsers.yaml_parser import load_yaml_to_dict
from ..parsers.json_parser import load_json_to_dict
from .utils import LoaderError, validate_data  # Import depuis utils

logger = logging.getLogger(__name__)

def load_yaml_or_json_data(input_dir: str, base_filename: str, required_keys: List[str] = None) -> Dict[str, Any]:
    """
    Charge les données d'un fichier (YAML/JSON) avec priorité YAML.
    Valide optionnellement les clés requises.
    """
    input_path = Path(input_dir)
    
    # Priorité YAML/YML
    for ext in ['.yml', '.yaml']:
        file_path = input_path / f'{base_filename}{ext}'
        if file_path.exists():
            logger.info(f"Chargement YAML : {file_path}")
            data = load_yaml_to_dict(str(file_path))
            if required_keys:
                validate_data(data, required_keys)
            return data
    
    # Fallback JSON
    json_file = input_path / f'{base_filename}.json'
    if json_file.exists():
        logger.info(f"Chargement JSON : {json_file}")
        data = load_json_to_dict(str(json_file))
        if required_keys:
            validate_data(data, required_keys)
        return data
    
    raise LoaderError(f"Fichier {base_filename} (YAML/JSON) manquant dans {input_dir}.")

def load_introduction_data(input_dir: str) -> Dict[str, Any]:
    required = ['version', 'metadata', 'principe_modelisation', 'modele_specifique']
    return load_yaml_or_json_data(input_dir, 'introduction', required_keys=required)

def load_user_manual_data(input_dir: str) -> Dict[str, Any]:
    required = ['version', 'metadata', 'lancement_simulation', 'entrees', 'sorties']
    return load_yaml_or_json_data(input_dir, 'user_manual', required_keys=required)