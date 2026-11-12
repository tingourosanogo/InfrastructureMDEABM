# src/loaders/utils.py

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class LoaderError(Exception):
    """Exception custom pour les erreurs de loading."""
    pass

def validate_data(data: Dict, required_keys: List[str]) -> None:
    """Valide que les clés requises sont présentes dans les données."""
    missing = [k for k in required_keys if k not in data]
    if missing:
        msg = f"Clés manquantes dans les données : {missing}"
        logger.warning(msg)
        raise LoaderError(msg)