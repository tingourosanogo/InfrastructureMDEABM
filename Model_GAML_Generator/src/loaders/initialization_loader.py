# src/loaders/initialization_loader.py

from typing import Dict, Any
from pathlib import Path
import logging
from ..parsers.csv_parser import InitializationCSVParser
from ..parsers.json_parser import load_json_to_dict
from ..parsers.yaml_parser import load_yaml_to_dict
from .utils import LoaderError, validate_data

logger = logging.getLogger(__name__)

def load_initialization_data(input_dir: str) -> Dict[str, Any]:
    """Charge les données d'initialisation (Multi-CSV > YAML/JSON). Valide la structure."""
    input_path = Path(input_dir)
    init_dir = input_path / 'initialization_data'
    base_filename = 'initialization'
    required_keys = ['metadata', 'global', 'input_data', 'entities', 'scenarios']
    
    # Priorité Multi-CSV (Répertoire)
    if init_dir.is_dir():
        logger.info(f"Chargement multi-CSV : {init_dir}")
        parser = InitializationCSVParser(csv_dir=str(init_dir))
        data = parser.convert_all()
        validate_data(data, required_keys)
        return data
    
    # Priorité YAML/YML
    for ext in ['.yml', '.yaml']:
        file_path = input_path / f'{base_filename}{ext}'
        if file_path.exists():
            logger.info(f"Chargement YAML : {file_path}")
            data = load_yaml_to_dict(str(file_path))
            validate_data(data, required_keys)
            return data
    
    # Fallback JSON
    json_file = input_path / f'{base_filename}.json'
    if json_file.exists():
        logger.info(f"Chargement JSON : {json_file}")
        data = load_json_to_dict(str(json_file))
        validate_data(data, required_keys)
        return data
    
    raise LoaderError(f"Ni répertoire initialization_data ni fichier {base_filename} (YAML/JSON) trouvés dans {input_dir}.")