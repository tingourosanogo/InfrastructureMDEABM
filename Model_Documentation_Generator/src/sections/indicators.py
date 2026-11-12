from .base import BaseSection
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class IndicatorsSection(BaseSection):
    """Génère la section Indicateurs au format Markdown"""

    # Constantes pour les messages
    DEFAULT_DESC = "*Description à compléter*"
    MISSING_DATA = "..."
    EMPTY_SECTION = "*Section vide : à compléter manuellement*"
    MISSING_DATA_MESSAGE = "*A compléter*"
    
    def __init__(self, data: Dict):
        super().__init__(data)
        self._validate_data()

    def _validate_data(self) -> None:
        """Valide la structure minimale des données"""
        required_fields = ['id', 'name', 'description']
        for indicator in self.data.get('indicators', []):
            for field in required_fields:
                if field not in indicator:
                    raise ValueError(f"Champ manquant '{field}' dans l'indicateur {indicator.get('id')}")

    def generate(self) -> str:
        """Génère le Markdown complet"""
        try:
            content = ["# Indicateurs\n"]
            
            # Par catégorie si présente
            if any('category' in ind for ind in self.data['indicators']):
                content.append(self._generate_by_category())
            else:
                content.extend(self._generate_indicator(ind) for ind in self.data['indicators'])
            
            return "\n".join(content)
        except Exception as e:
            logger.error(f"ERREUR GENERATION INDICATEURS: {str(e)}")
            return "# Indicateurs\n\n*Erreur de génération*"

    def _generate_by_category(self) -> str:
        """Groupe les indicateurs par catégorie"""
        categories = {}
        for ind in self.data['indicators']:
            cat = ind.get('category', 'Non catégorisé')
            categories.setdefault(cat, []).append(ind)
        
        content = []
        for cat, indicators in categories.items():
            content.append(f"## {cat}\n")
            content.extend(self._generate_indicator(ind) for ind in indicators)
        
        return "\n".join(content)

    def _generate_indicator(self, indicator: Dict) -> str:
        """Génère le Markdown pour un indicateur"""
        var = indicator.get('variables', [])
        params = indicator.get('parameters', [])
        sections = [
            f"\n### Indicateur {indicator['id']} : {indicator['name']} ({indicator['unit']})",
            self._generate_description(indicator)
        ]
        sections.append(self._generate_formula(indicator))
        sections.append("\n#### Attributs ")
        sections.append(self._generate_variables(var))
        sections.append(self._generate_parameters(params))
        return "\n\n".join(filter(None, sections))

    def _generate_description(self, indicator: Dict) -> str:
        return f"\n#### Description \n\n{indicator.get('description', self.MISSING_DATA_MESSAGE)}"

    def _generate_formula(self, indicator: Dict) -> str:
        if not indicator.get('formula'):
            return f"#### Calcul \n\n {self.MISSING_DATA_MESSAGE}"
        return f"\n#### Calcul \n\n```math\n{indicator['formula']}\n```"

    def _generate_variables(self, variables: List[Dict]) -> str:
     
        headers = ["variables", "Entité", "Description", "Unité"]
    
        # En-tête du tableau
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
    
        # Lignes de données
        rows = []
        for par in variables:
            rows.append(
                f"| {par.get('name', '?')} | "
                f"{par.get('entity', '')} | "
                f"{par.get('definition', '')} |"
                f"{par.get('unit', '')} |"
            )
        
    
        # Si pas de données, ajouter une ligne vide
        if not rows:
            rows.append(f"| {' | '.join(['...'] * len(headers))} |")
    
        return "\n\nL’indicateur dépend des variables suivantes : \n\n "+ "\n".join([header_row, separator] + rows)

    def _generate_parameters(self, parameters: List[Dict]) -> str:
     
        headers = ["Paramètres", "Entité", "Description", "Unité", "Valeur"]
    
        # En-tête du tableau
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
    
        # Lignes de données
        rows = []
        for par in parameters:
            rows.append(
                f"| {par.get('name', '?')} | "
                f"{par.get('entity', '')} | "
                f"{par.get('definition', '')} |"
                f"{par.get('unit', '')} |"
                f"{par.get('value', '')} |"
            )
    
        # Si pas de données, ajouter une ligne vide
        if not rows:
            rows.append(f"| {' | '.join(['...'] * len(headers))} |")
    
        return "\n\nEt dépend des paramètres suivants \n\n "+ "\n".join([header_row, separator] + rows)