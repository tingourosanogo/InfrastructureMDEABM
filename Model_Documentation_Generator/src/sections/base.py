from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseSection(ABC):
    def __init__(self, data: Dict[str, Any], config: Dict[str, Any] = None):
        self.data = data
        self.config = config or {}

    @abstractmethod
    def generate(self) -> str:
        """Génère le contenu Markdown de la section"""
        pass

    def _safe_get(self, data: Dict, key: str, default: Any = None) -> Any:
        """Accès sécurisé aux données"""
        return data.get(key, default)