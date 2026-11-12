# src/loaders/indicator_loader.py

from typing import List, Dict
from pathlib import Path
import logging
from ..parsers.csv_parser import load_indicator_csv
from ..parsers.json_parser import load_json_to_dict
from ..parsers.yaml_parser import load_yaml_to_dict
from .utils import LoaderError

logger = logging.getLogger(__name__)

def load_indicator_data(input_dir: str) -> List[Dict]:
    """Charge les indicateurs (CSV > YAML/JSON). Valide basiquement."""
    input_path = Path(input_dir)
    base_filename = 'indicators'
    
    # Priorité CSV
    csv_file = input_path / f'{base_filename}.csv'
    if csv_file.exists():
        logger.info(f"Chargement CSV : {csv_file}")
        data = load_indicator_csv(str(csv_file))
        _validate_indicators(data)
        return data
    
    # Priorité YAML/YML
    for ext in ['.yml', '.yaml']:
        file_path = input_path / f'{base_filename}{ext}'
        if file_path.exists():
            logger.info(f"Chargement YAML : {file_path}")
            data = load_yaml_to_dict(str(file_path)).get('indicators', [])
            _validate_indicators(data)
            return data
    
    # Fallback JSON
    json_file = input_path / f'{base_filename}.json'
    if json_file.exists():
        logger.info(f"Chargement JSON : {json_file}")
        data = load_json_to_dict(str(json_file)).get('indicators', [])
        _validate_indicators(data)
        return data
    
    raise LoaderError(f"Fichier {base_filename} (CSV/YAML/JSON) manquant dans {input_dir}.")

def _validate_indicators(indicators: List[Dict]) -> None:
    """Validation basique : Au moins un indicateur, et clés requises par item."""
    if not indicators:
        raise LoaderError("Liste d'indicateurs vide.")
    required_per_item = ['id', 'name', 'formula']
    for ind in indicators:
        missing = [k for k in required_per_item if k not in ind]
        if missing:
            logger.warning(f"Indicateur incomplet (id={ind.get('id', 'inconnu')}) : clés manquantes {missing}")