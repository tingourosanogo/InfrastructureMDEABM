# src/loaders/loader_master.py

import logging
from typing import Dict, Any, Callable, List
from pathlib import Path
from .utils import LoaderError  # Import depuis utils

# Importation des loaders spécifiques
from .generic_yaml_json_loader import load_introduction_data, load_user_manual_data
from .initialization_loader import load_initialization_data
from .indicator_loader import load_indicator_data

logger = logging.getLogger(__name__)

# Registry des loaders
LOADERS_REGISTRY: Dict[str, Callable[[str], Any]] = {
    'introduction': load_introduction_data,
    'user_manual': load_user_manual_data,
    'initialization': load_initialization_data,
    'indicators': load_indicator_data,
}

def load_source(source_type: str, input_dir: str) -> Any:
    """
    Loader master : Charge une source spécifique via le registry.
    Raise LoaderError si type inconnu ou échec.
    """
    if source_type not in LOADERS_REGISTRY:
        raise LoaderError(f"Type de source inconnu : {source_type}. Types disponibles : {list(LOADERS_REGISTRY.keys())}")
    
    loader_func = LOADERS_REGISTRY[source_type]
    try:
        data = loader_func(input_dir)
        if not data:
            logger.warning(f"Données vides pour {source_type} dans {input_dir}.")
        return data
    except Exception as e:
        logger.error(f"Erreur lors du loading de {source_type} : {str(e)}")
        raise LoaderError(f"Échec du loading pour {source_type} : {str(e)}") from e
    
'''
# Fonction pour valider les données contre un template basique (dict de clés requises)
def validate_data(data: Dict, required_keys: List[str]) -> None:
    missing = [k for k in required_keys if k not in data]
    if missing:
        msg = f"Clés manquantes dans les données : {missing}"
        logger.warning(msg)
        raise LoaderError(msg) 
'''