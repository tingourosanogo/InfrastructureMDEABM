import logging
from typing import Dict
from pathlib import Path
import sys

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import DocConfig
from src.exceptions import DocumentationError
from src.sections.structure import StructureSection

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentationBuilder:
    def __init__(self, config: DocConfig):
        self.config = config
        #logger.info("Builder DSL initialisé avec config: %s", config)

    def build(self, parser) -> str:
        """Construit la documentation Markdown pour notre DSL"""
        try:
            # 1. Vérification parser
            if not hasattr(parser, "parse_to_structure"):
                raise AttributeError("Le parser doit implémenter parse_to_structure()")

            # 2. Parsing
            data = parser.parse_to_structure()
            #logger.debug("Données parsées DSL: %s", data)

            # 3. Validation données DSL
            required_keys = ["ecosystem", "entities", "processes"]
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Section manquante dans le modèle DSL: {key}")

            if not isinstance(data["entities"], dict):
                raise ValueError("La section 'entities' doit être un dictionnaire (agents/resources/parameters)")

            # Vérification sous-sections
            for sub in ["agents", "resources", "parameters"]:
                if sub not in data["entities"]:
                    raise ValueError(f"Sous-section manquante dans entities: {sub}")

            if not isinstance(data["processes"], list):
                raise ValueError("La section 'processes' doit être une liste")

            # 4. Génération Markdown
            section = StructureSection(data=data)
            content = section.generate()

            # 5. Validation sortie
            if not content or not content.strip():
                raise ValueError("Contenu Markdown vide")

            return content

        except Exception as e:
            logger.error("Échec de génération DSL", exc_info=True)
            raise DocumentationError(f"Erreur lors de la génération DSL: {str(e)}")
