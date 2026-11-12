from .base import BaseSection
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class InitializationSection(BaseSection):
    """Génère la section Initialisation au format Markdown - ODD Compliant"""

    # Constantes pour les messages
    DEFAULT_DESC = "*Description à compléter*"
    MISSING_DATA = "..."
    EMPTY_SECTION = "*Section à compléter manuellement*"
    MISSING_DATA_MESSAGE = "*A compléter*"
    
    def __init__(self, data: Dict):
        super().__init__(data)
        self._validate_data()

    def _validate_data(self) -> None:
        """Valide la structure minimale des données d'initialisation"""
        if not isinstance(self.data, dict):
            raise ValueError("Les données d'initialisation doivent être un dictionnaire")
        
        # Vérifie la présence des sections clés ODD
        '''
        expected_sections = ['entities', 'parameters', 'state_variables']
        for section in expected_sections:
            if section not in self.data:
                logger.warning(f"Section '{section}' manquante dans les données d'initialisation")
        '''
    def generate(self) -> str:
        """Génère le Markdown complet pour la section Initialisation"""
        try:
            """Charger les données de JSON"""
            #_metadata = self.data.get('metadata', [])
            _initialisation = self.data.get('global', {})
            _input_data     = self.data.get('input_data', {})
            _entities = self.data.get('entities', {})
            _parameters = self.data.get('parameters', {})
            _state_vars = self.data.get('state_variables', {})
            _scenarios = self.data.get('scenarios', [])
            #_data_sources = self.data.get('data_sources', [])
            #_validation_metrics = self.data.get('validation', [])
            _initialization_rules = self.data.get('initialization_rules', [])
            content = [
                "# Initialisation",
                # self._generate_metadata(_metadata),
                self._generate_general_Init(_initialisation),
                self._generate_input_data(_input_data),
                self._generate_entities(_entities),
                self._generate_parameters(_parameters),
                self._generate_state_variables(_state_vars),
                self._generate_scenarios(_scenarios),
                #self._generate_data_sources(_data_sources),
                #self._generate_validation(_validation_metrics)
                self._generate_initialization_rules(_initialization_rules)
            ]
            
            return "\n\n".join(filter(None, content))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION INITIALISATION: {str(e)}")
            return "# Initialisation\n\n*Erreur de génération de la section*"
    
        '''
    def _generate_metadata(self, metadata: Dict) -> str:
        """Génère la section métadonnées"""
        if not metadata:
            return None
            
        content = ["## Métadonnées\n"]
        for item in metadata:
            if isinstance(item, dict) and 'key' in item and 'value' in item:
                content.append(f"- **{item['key']}** : {item.get('value', self.MISSING_DATA)}")
                if 'description' in item:
                    content.append(f"  *{item['description']}*")
        
        return "\n".join(content) if len(content) > 1 else None
    '''
    def _generate_general_Init(self, _initialisation: Dict) -> str:
        """Génère le Markdown complet pour la sous-section Initialisation"""
        try:
            if not _initialisation:
                return self._generate_empty_section()
            
            content = [
                "## Initialisation",
                self._generate_temporal_scope(_initialisation.get('temporal_scope', {})),
                self._generate_spatial_configuration(_initialisation.get('spatial_configuration', {})),
                #self._generate_additional_config()
            ]
            
            return "\n\n".join(filter(None, content))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION INITIALISATION: {str(e)}")
            return "## Initialisation\n\n*Erreur de génération de la section*"

    def _generate_empty_section(self) -> str:
        """Génère une section vide avec message d'instruction"""
        return """## Initialisation

### Portée Temporelle
*Configuration temporelle à compléter.*

### Configuration Spatiale  
*Configuration spatiale à compléter.*"""

    def _generate_temporal_scope(self, temporal: Dict) -> str:
        """Génère la portée temporelle"""
        if not temporal:
            return None
        
        content = [
            "### Portée Temporelle",
            "Configuration de la dimension temporelle de la simulation :\n"
        ]
        headers = ["Paramètre", "Valeur", "Description"]
    
        # En-tête du tableau
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        # Lignes de données
        temporal_params = [
            ("Date de début", temporal.get('start_date', self.MISSING_DATA), "Date initiale de la simulation"),
            ("Date de fin", temporal.get('end_date', self.MISSING_DATA), "Date finale de la simulation"),
            ("Pas de temps", temporal.get('time_step', self.MISSING_DATA), "Incrément temporel de simulation"),
            ("Période de chauffe", temporal.get('warmup_period', self.MISSING_DATA), "Période d'initialisation avant collecte des données")
        ]

        rows = []
        for param, value, desc in temporal_params:
            rows.append(f"| {param} | `{value}` | {desc} |")
       
        content.extend([header_row, separator] + rows)
        return "\n".join(content)


    def _generate_spatial_configuration(self, spatial: Dict) -> str:
        """Génère la configuration spatiale"""
        
        if not spatial:
            return None
        
        content = [
            "### Configuration Spatiale",
            "Configuration de la dimension spatiale de la simulation :\n"
        ]
        headers = ["Paramètre", "Valeur", "Description"]
    
        # En-tête du tableau
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        # Extent formaté
        extent = spatial.get('extent', [])
        extent_str = ', '.join(map(str, extent)) if extent else self.MISSING_DATA
        
        spatial_params = [
            ("Extension", f"[{extent_str}]", "Bounding box de la zone d'étude"),
            ("Projection", spatial.get('projection', self.MISSING_DATA), "Système de coordonnées de référence"),
            ("Résolution", spatial.get('resolution', self.MISSING_DATA), "Résolution spatiale des données")
        ]
        
        rows = []
        for param, value, desc in spatial_params:
            rows.append(f"| {param} | `{value}` | {desc} |")
        
        content.extend([header_row, separator] + rows)
        return "\n".join(content)
    

    def _generate_input_data(self, input_data: Dict) -> str:
        """Génère le Markdown complet pour la sous-section Données d'Entrée"""
        try:
            if not self._has_data(input_data):
                return self._generate_empty_section_id()
            
            _spatial_data = input_data.get('spatial_data', [])
            _tabular_data = input_data.get('tabular_data', [])
            content = [
                "## Données d'Entrée",
                self._generate_introduction_id(),
                self._generate_spatial_data(_spatial_data),
                self._generate_tabular_data(_tabular_data),
                #self._generate_quality_assessment()
            ]
            
            return "\n\n".join(filter(None, content))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION INITIALISATION - DONNEES: {str(e)}")
            return "## Données d'Entrée\n\n*Erreur de génération de la section*"

    def _has_data(self, input_data: Dict) -> bool:
        """Vérifie s'il y a des données à afficher"""
        return any(input_data.get(key) for key in ['spatial_data', 'tabular_data', 'other_data'])

    def _generate_empty_section_id(self) -> str:
        """Génère une section vide avec message d'instruction"""
        return """## Données d'Entrée

### Documentation

Description des différentes sources de données utilisées pour l'initialisation du modèle.

Cette section recense l'ensemble des données d'entrée nécessaires au fonctionnement du modèle, incluant les données spatiales, tabulaires et autres sources de données.

### Liste des Données

*Aucune donnée d'entrée définie pour le moment.*"""

    def _generate_introduction_id(self) -> str:
        """Génère l'introduction de la section"""
        return """### Documentation

Description des différentes sources de données utilisées pour l'initialisation du modèle.

Cette section recense l'ensemble des données d'entrée nécessaires au fonctionnement du modèle, incluant les données spatiales, tabulaires et autres sources de données."""

    def _generate_spatial_data(self, spatial_data: List[Dict]) -> Optional[str]:
        """Génère la section des données spatiales"""
        if not spatial_data:
            return None
            
        content = ["### Données Spatiales\n"]
        
        headers = ["Type", "Format", "Chemin", "Description", "Résolution", "Qualité"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        rows = []
        for data in spatial_data:
            rows.append(
                f"| {data.get('type', self.MISSING_DATA)} | "
                f"{data.get('format', self.MISSING_DATA)} | "
                f"`{data.get('path', self.MISSING_DATA)}` | "
                f"{data.get('description', self.MISSING_DATA)} | "
                f"{data.get('resolution', self.MISSING_DATA)} | "
                f"{data.get('uncertainty', data.get('reliability', self.MISSING_DATA))} |"
            )
        
        content.extend([header_row, separator] + rows)
        return "\n".join(content)

    def _generate_tabular_data(self, tabular_data: List[Dict]) -> Optional[str]:
        """Génère la section des données tabulaires"""
        if not tabular_data:
            return None
            
        content = ["### Données Tabulaires\n"]
        
        headers = ["Type", "Format", "Chemin", "Description", "Taille", "Taux Réponse", "Validation"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        rows = []
        for data in tabular_data:
            sample_size = data.get('sample_size', '')
            sample_str = f"{sample_size}" if sample_size else self.MISSING_DATA
            
            response_rate = data.get('response_rate', '')
            response_str = f"{response_rate}%" if response_rate else self.MISSING_DATA
            
            rows.append(
                f"| {data.get('type', self.MISSING_DATA)} | "
                f"{data.get('format', self.MISSING_DATA)} | "
                f"`{data.get('path', self.MISSING_DATA)}` | "
                f"{data.get('description', self.MISSING_DATA)} | "
                f"{sample_str} | "
                f"{response_str} | "
                f"{data.get('validation_method', self.MISSING_DATA)} |"
            )
        
        content.extend([header_row, separator] + rows)
        return "\n".join(content)

    def _generate_entities(self, entities: Dict) -> str:
        """Génère le Markdown complet pour la sous-section Entités"""
        try:
            if not entities:
                return self._generate_empty_section_en()
            
            content = [
                "## Entités",
                self._generate_introduction_en(),
                self._generate_entities_table(entities),
                self._generate_detailed_entities(entities)
            ]
            
            return "\n\n".join(filter(None, content))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION INITIALISATION - ENTITES: {str(e)}")
            return "## Entités\n\n*Erreur de génération de la section*"

    def _generate_empty_section_en(self) -> str:
        """Génère une section vide avec message d'instruction"""
        return """## Entités

### Documentation

Description des entités, agents et objets du modèle.

Cette section spécifie comment chaque entité est initialisée et quelles données sont utilisées pour leur création.

### Liste des Entités

*Aucune entité définie pour le moment.*"""

    def _generate_introduction_en(self) -> str:
        """Génère l'introduction de la section entités"""
        return """### Documentation

Description des entités, agents et objets du modèle.

Cette section spécifie comment chaque entité est initialisée et quelles données sont utilisées pour leur création."""

    def _generate_entities_table(self, entities: Dict) -> str:
        """Génère le tableau récapitulatif des entités"""
        content = ["### Liste des Entités\n"]
        
        headers = ["Nom", "Type", "Effectif", "Méthode d'Initialisation"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        rows = []
        for entity in entities:
            count = entity.get('count', 'N/A')
            if count is None:
                count = 'N/A'
            
            rows.append(
                f"| **{entity.get('name', '?')}** | "
                f"{entity.get('type', self.MISSING_DATA)} | "
                f"{count} | "
                f"{entity.get('initialization_method', self.MISSING_DATA)} | "
            )
        
        content.extend([header_row, separator] + rows)
        return "\n".join(content)

    def _generate_detailed_entities(self, entities: Dict) -> str:
        """Génère les détails de chaque entité"""
        content = ["### Détails par Entité\n"]
        
        for entity in entities:
            content.append(self._generate_single_entity(entity))
        
        return "\n\n".join(content)

    def _generate_single_entity(self, entity: Dict) -> str:
        """Génère les détails d'une entité spécifique"""
        entity_content = [
            f"#### Entité : {entity.get('name', 'Sans nom')}",
            f"**Type** : {entity.get('type', '**Non spécifié**')}"
        ]
        
        # Effectif si applicable
        count = entity.get('count')
        if count is not None:
            entity_content.append(f"\n**Effectif** : {count}")
        
        # Méthode d'initialisation
        init_method = entity.get('initialization_method')
        if init_method:
            entity_content.append(f"\n**Méthode d'initialisation** : `{init_method}`")
        
        # Source de données
        data_source = entity.get('data_source')
        if data_source:
            entity_content.append(f"\n**Source de données** : `{data_source}`")
        
        # Stratégie d'échantillonnage
        sampling = entity.get('sampling_strategy')
        if sampling:
            entity_content.append(f"\n**Stratégie d'échantillonnage** : `{sampling}`")
        
        # Variables de stratification
        stratification_vars = entity.get('stratification_variables', [])
        if stratification_vars:
            vars_str = ", ".join([f"`{var}`" for var in stratification_vars])
            entity_content.append(f"\n**Variables de stratification** : {vars_str}")
        
        # Mapping d'attributs
        attribute_mapping = entity.get('attribute_mapping', [])
        if attribute_mapping:
            entity_content.append("\n**Mapping d'attributs :**")
            for mapping in attribute_mapping:
                if isinstance(mapping, dict):
                    map_str = f"`{mapping.get('model_attribute', '?')}` ← `{mapping.get('data_field', '?')}`"
                    if mapping.get('conversion'):
                        map_str += f" (conversion: `{mapping['conversion']}`)"
                    entity_content.append(f"- {map_str}")
                else:
                    entity_content.append(f"- `{mapping}`")
        
        # Description supplémentaire si disponible
        description = entity.get('description')
        if description:
            entity_content.append(f"\n**Description** : {description}")
        
        return "\n".join(entity_content)

    def _generate_parameters(self, _parameters: Dict) -> str:
        """Génère le Markdown complet pour la sous-section Paramètres"""
        try:
            _fixed_params = _parameters.get('fixed', [])
            _variable_params = _parameters.get('variable', [])
            content = [
                "## Paramètres",
                self._generate_introduction_pa(),
                self._generate_fixed_parameters(_fixed_params),
                self._generate_variable_parameters(_variable_params),
                #self._generate_uncertainty_section()
            ]
            
            return "\n\n".join(filter(None, content))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION INITIALISATION - PARAMETRES: {str(e)}")
            return "## Paramètres\n\n*Erreur de génération de la section*"

    def _generate_introduction_pa(self) -> str:
        """Génère l'introduction de la section paramètres"""
        return """### Documentation

Cette section présente l'ensemble des paramètres du modèle, divisés en deux catégories :

- **Paramètres fixes (Z)** : Valeurs constantes pour toutes les simulations
- **Paramètres variables (X)** : Valeurs à explorer dans les scénarios"""

    def _generate_fixed_parameters(self, fixed_params: List[Dict]) -> Optional[str]:
        """Génère la section des paramètres fixes"""
        if not fixed_params:
            return None
            
        content = [
            "### Paramètres Fixes (Z)",
            "Paramètres dont la valeur est constante pour toutes les simulations :\n",
            self._generate_parameters_table(fixed_params, is_fixed=True)
        ]
        
        return "\n".join(content)

    def _generate_variable_parameters(self, variable_params: List[Dict]) -> Optional[str]:
        """Génère la section des paramètres variables"""
        if not variable_params:
            return None
            
        content = [
            "### Paramètres Variables (X)",
            "Paramètres à explorer dans les scénarios :\n",
            self._generate_parameters_table(variable_params, is_fixed=False)
        ]
        
        return "\n".join(content)

    def _generate_parameters_table(self, parameters: List[Dict], is_fixed: bool = True) -> str:
        """Génère une table de paramètres"""
        if is_fixed:
            headers = ["Paramètre", "Entité", "Définition", "Unité", "Valeur", "Incertitude", "Sensibilité"]
        else:
            headers = ["Paramètre", "Entité", "Définition", "Unité", "Valeurs", "Impact"]
        
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        rows = []
        for param in parameters:
            if is_fixed:
                # Paramètres fixes
                uncertainty_info = self._format_uncertainty(param.get('uncertainty', {}))
                sensitivity = param.get('sensitivity_rank', self.MISSING_DATA)
                
                rows.append(
                    f"| `{param.get('name', '?')}` | "
                    f"{param.get('entity', self.MISSING_DATA)} | "
                    f"{param.get('definition', self.MISSING_DATA)} | "
                    f"{param.get('unit', self.MISSING_DATA)} | "
                    f"**{param.get('value', self.MISSING_DATA)}** | "
                    f"{uncertainty_info} | "
                    f"{sensitivity} |"
                )
            else:
                # Paramètres variables
                values = param.get('values', [])
                values_str = ', '.join(map(str, values)) if values else self.MISSING_DATA
                impact = param.get('impact_assessment', self.MISSING_DATA)
                
                rows.append(
                    f"| `{param.get('name', '?')}` | "
                    f"{param.get('entity', self.MISSING_DATA)} | "
                    f"{param.get('definition', self.MISSING_DATA)} | "
                    f"{param.get('unit', self.MISSING_DATA)} | "
                    f"**{values_str}** | "
                    f"{impact} |"
                )
        
        if not rows:
            no_data_row = f"| {' | '.join([self.MISSING_DATA] * len(headers))} |"
            rows.append(no_data_row)
        
        return "\n".join([header_row, separator] + rows)

    def _format_uncertainty(self, uncertainty: Dict) -> str:
        """Formate les informations d'incertitude"""
        if not uncertainty:
            return "Non quantifié"
        
        parts = []
        if 'distribution' in uncertainty:
            parts.append(f"Dist: {uncertainty['distribution']}")
        if 'std_dev' in uncertainty:
            parts.append(f"σ: {uncertainty['std_dev']}")
        if 'range' in uncertainty:
            parts.append(f"Range: {uncertainty['range']}")
        
        return ', '.join(parts) if parts else "Spécifié"

    def _generate_state_variables(self, state_vars: Dict) -> str:
        """Génère le Markdown complet pour la sous-section Variables d'état"""
        try:
            _fixed_variables = state_vars.get('fixed_initialization', [])
            _variable_variables = state_vars.get('variable_initialization', [])
            content = [
                "## Variables d'État Initiales",
                self._generate_introduction_ve(),
                self._generate_fixed_variables(_fixed_variables),
                self._generate_variable_variables(_variable_variables)
            ]
            
            return "\n\n".join(filter(None, content))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION INITIALISATION - VARIABLES: {str(e)}")
            return "## Variables d'État Initiales\n\n*Erreur de génération de la section*"

    def _generate_introduction_ve(self) -> str:
        """Génère l'introduction de la section"""
        return """### Documentation

Les variables d'état représentent l'état initial du système au début de la simulation.

**Variables fixes** : Valeurs initiales constantes pour toutes les simulations  
**Variables variables** : Plages de valeurs à explorer dans les scénarios"""

    def _generate_fixed_variables(self, fixed_vars = List[Dict]) -> Optional[str]:
        """Génère la section des variables fixes"""
        if not fixed_vars:
            return None
            
        content = [
            "### Variables d'État Fixes",
            "Valeurs initiales constantes pour toutes les simulations :\n"
        ]
        
        headers = ["Variable", "Entité", "Valeur", "Unité", "Distribution", "Paramètres"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        rows = []
        for var in fixed_vars:
            # Formatage des paramètres de distribution
            params = var.get('parameters', {})
            params_str = self._format_parameters(params)
            
            rows.append(
                f"| `{var.get('name', '?')}` | "
                f"{var.get('entity', self.MISSING_DATA)} | "
                f"**{var.get('value', self.MISSING_DATA)}** | "
                f"{var.get('unit', self.MISSING_DATA)} | "
                f"{var.get('distribution', self.MISSING_DATA)} | "
                f"{params_str} | "
            )
        
        content.extend([header_row, separator] + rows)
        return "\n".join(content)

    def _generate_variable_variables(self, variable_vars = List[Dict]) -> Optional[str]:
        """Génère la section des variables variables"""
        if not variable_vars:
            return None
            
        content = [
            "### Variables d'État Variables",
            "Plages de valeurs initiales à explorer dans les scénarios :\n"
        ]
        
        headers = ["Variable", "Entité", "Valeurs", "Unité", "Distribution", "Probabilités"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        rows = []
        for var in variable_vars:
            # Formatage des valeurs et probabilités
            values = var.get('values', [])
            values_str = self._format_list(values)
            
            probs = var.get('probabilities', [])
            probs_str = self._format_list(probs, is_prob=True)
            
            rows.append(
                f"| `{var.get('name', '?')}` | "
                f"{var.get('entity', self.MISSING_DATA)} | "
                f"{values_str} | "
                f"{var.get('unit', self.MISSING_DATA)} | "
                f"{var.get('distribution', self.MISSING_DATA)} | "
                f"{probs_str} | "
            )
        
        content.extend([header_row, separator] + rows)
        return "\n".join(content)

    def _format_parameters(self, params: Dict[str, Any]) -> str:
        """Formate les paramètres de distribution pour l'affichage"""
        if not params:
            return self.MISSING_DATA
        
        param_strings = []
        for key, value in params.items():
            param_strings.append(f"{key}={value}")
        
        return ", ".join(param_strings)

    def _format_list(self, items: List[Any], is_prob: bool = False) -> str:
        """Formate une liste de valeurs pour l'affichage tableau"""
        if not items:
            return self.MISSING_DATA
        
        if is_prob:
            # Pour les probabilités, on formatte avec 2 décimales
            formatted_items = [f"{float(item):.2f}" for item in items]
        else:
            formatted_items = [str(item) for item in items]
        
        if len(formatted_items) <= 3:
            return ", ".join(formatted_items)
        else:
            return f"{', '.join(formatted_items[:2])}, ..., {formatted_items[-1]}"
    

    def _generate_scenarios(self, scenarios: List[Dict]) -> str:
        """Génère le Markdown complet pour la sous-section Scénarios"""
        try:
            if not scenarios:
                return self._generate_empty_section_sc()
            
            content = [
                "## Scénarios",
                self._generate_introduction_sc(),
                #self._generate_scenarios_table(scenarios),
                self._generate_detailed_scenarios(scenarios)
            ]
            
            return "\n\n".join(filter(None, content))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION INITIALISATION - SCENARIOS: {str(e)}")
            return "## Scénarios\n\n*Erreur de génération de la section*"


    def _generate_empty_section_sc(self) -> str:
        """Génère une section vide avec message d'instruction"""
        return """## Scénarios

### Documentation

Description des scénarios que l'on veut explorer avec justifications et références éventuelles.

Un scénario est défini par l'attribution de valeurs à un sous-ensemble X des paramètres et variables énumérées dans la section Initialisation.

### Liste des Scénarios

*Aucun scénario défini pour le moment.*"""


    def _generate_introduction_sc(self) -> str:
        """Génère l'introduction de la section scénarios"""
        return """### Documentation

Description des scénarios que l'on veut explorer avec justifications et références éventuelles.

Un scénario est défini par l'attribution de valeurs à un sous-ensemble X des paramètres et variables énumérées dans la section Initialisation."""


    def _generate_scenarios_table(self, scenarios: List[Dict]) -> str:
        """Génère le tableau récapitulatif des scénarios"""
        content = ["### Liste des Scénarios\n"]
        
        headers = ["Nom", "Description", "Base", "Paramètres Clés", "Statut Validation"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        rows = []
        for scenario in scenarios:
            # Extraction des paramètres clés
            key_params = []
            params = scenario.get('parameters', {})
            if params:
                for param_name, param_value in params.items():
                    key_params.append(f"{param_name}: {param_value}")
            
            rows.append(
                f"| **{scenario.get('name', '?')}** | "
                f"{scenario.get('description', self.MISSING_DATA)} | "
                f"{scenario.get('based_on', self.MISSING_DATA)} | "
                f"{'; '.join(key_params) if key_params else self.MISSING_DATA} | "
                f"{scenario.get('validation_status', self.MISSING_DATA)} |"
            )
        
        content.extend([header_row, separator] + rows)
        return "\n".join(content)


    def _generate_detailed_scenarios(self, scenarios: List[Dict]) -> str:
        """Génère les détails de chaque scénario"""
        content = ["### Détails par Scénario\n"]
        
        for scenario in scenarios:
            content.append(self._generate_single_scenario(scenario))
        
        return "\n\n".join(content)

    def _generate_single_scenario(self, scenario: Dict) -> str:
        """Génère les détails d'un scénario spécifique"""
        scenario_content = [
            f"#### Scénario : {scenario.get('name', 'Sans nom')}",
            f"\n**Description** : {scenario.get('description', self.DEFAULT_DESC)}",
            f"\n**Base** : {scenario.get('based_on', 'Non spécifié')}",
            f"\n**Statut de validation** : {scenario.get('validation_status', 'Non validé')}"
        ]
        
        # Section Paramètres
        parameters = scenario.get('parameters', {})
        if parameters:
            scenario_content.append("\n**Paramètres :**")
            for param_name, param_value in parameters.items():
                scenario_content.append(f"- `{param_name}` = `{param_value}`")
        
        # Section Variables d'état
        state_vars = scenario.get('state_variables', {})
        if state_vars:
            scenario_content.append("\n**Variables d'état initiales :**")
            for var_name, var_value in state_vars.items():
                scenario_content.append(f"- `{var_name}` = `{var_value}`")
        
        return "\n".join(scenario_content)


    def _generate_initialization_rules(self, init_rules: List[Dict]) -> str:
        """Génère le Markdown complet pour la sous-section Règles d'initialisation"""
        try:
            if not init_rules:
                return self._generate_empty_section_ir()
            
            content = [
                "## Règles d'Initialisation",
                self._generate_introduction_ir(),
                self._generate_rules_table(init_rules),
                self._generate_detailed_rules(init_rules)
            ]
            
            return "\n\n".join(filter(None, content))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION REGLES D'INITIALISATION: {str(e)}")
            return "## Règles d'Initialisation\n\n*Erreur de génération de la section*"


    def _generate_empty_section_ir(self) -> str:
        """Génère une section vide avec message d'instruction"""
        return """## Règles d'Initialisation

### Documentation

Description des règles et méthodes utilisées pour initialiser les entités du modèle.

Les règles d'initialisation définissent comment les valeurs initiales sont attribuées aux différentes entités et variables du modèle.

### Liste des Règles

*Aucune règle d'initialisation définie pour le moment.*"""

    def _generate_introduction_ir(self) -> str:
        """Génère l'introduction de la section règles d'initialisation"""
        return """### Documentation

Description des règles et méthodes utilisées pour initialiser les entités du modèle.

Les règles d'initialisation définissent comment les valeurs initiales sont attribuées aux différentes entités et variables du modèle, incluant les distributions statistiques, les méthodes de calcul et les hypothèses sous-jacentes."""

    def _generate_rules_table(self, init_rules: List[Dict]) -> str:
        """Génère le tableau récapitulatif des règles"""
        content = ["### Liste des Règles d'Initialisation\n"]
        
        headers = ["Entité", "Règle", "Implémentation", "Hypothèses"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        rows = []
        for rule in init_rules:
            # Formatage des cellules pour le tableau
            rule_display = f"`{rule.get('rule', self.MISSING_DATA)}`"
            impl_display = f"`{rule.get('implementation', self.MISSING_DATA)}`"
            assumptions_display = f"`{rule.get('assumptions', self.MISSING_DATA)}`"
            
            rows.append(
                f"| **{rule.get('entity', '?')}** | "
                f"{rule_display} | "
                f"{impl_display} | "
                f"{assumptions_display} |"
            )
        
        content.extend([header_row, separator] + rows)
        return "\n".join(content)


    def _generate_detailed_rules(self, init_rules: List[Dict]) -> str:
        """Génère les détails de chaque règle"""
        content = ["### Détails par Règle\n"]
        
        for i, rule in enumerate(init_rules, 1):
            content.append(self._generate_single_rule(rule, i))
        
        return "\n\n".join(content)

    def _generate_single_rule(self, rule: Dict, index: int) -> str:
        """Génère les détails d'une règle spécifique"""
        rule_content = [
            f"#### Règle {index} : {rule.get('entity', 'Entité inconnue')}",
            f"**Règle mathématique** :",
            f"```math\n{rule.get('rule', self.MISSING_DATA)}\n```"
        ]
        
        # Implémentation code
        implementation = rule.get('implementation')
        if implementation:
            rule_content.extend([
                "\n**Implémentation code** :",
                f"```python\n{implementation}\n```"
            ])
        else:
            rule_content.append(f"\n**Implémentation** : *Implémentation non spécifiée*")
        
        # Hypothèses
        assumptions = rule.get('assumptions')
        if assumptions:
            rule_content.extend([
                "\n**Hypothèses et justifications** :",
                f"{assumptions}"
            ])
        else:
            rule_content.append(f"\n**Hypothèses** : *Aucune hypothèse spécifiée*")
                
        return "\n".join(rule_content)


    def _generate_data_sources(self, data_sources: Dict) -> str:
        """Génère la section sources de données"""
        if not data_sources:
            return None
            
        content = [
            "## Sources de Données",
            "### Provenance et Qualité des Données\n"
        ]
        
        headers = ["Source", "Type", "Description", "Fiabilité", "Usage"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        rows = []
        for source in data_sources:
            rows.append(
                f"| {source.get('description', '?')} | "
                f"{source.get('data_type', '')} | "
                f"{source.get('path', '')} | "
                f"{source.get('reliability', '')} | "
                f"{source.get('usage', '')} |"
            )
        
        if not rows:
            rows.append(f"| {' | '.join([self.MISSING_DATA] * len(headers))} |")
        
        content.extend([header_row, separator] + rows)
        return "\n".join(content)




    def _generate_validation(self,  validation_metrics: Dict) -> Optional[str]:
        """Génère la section validation"""
        if not validation_metrics:
            return None
            
        content = [
            "## Validation et Incertitudes",
            "### Métriques de Validation\n"
        ]
        
        headers = ["Paramètre", "Méthode", "Métrique", "Valeur", "Seuil", "Statut"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        
        rows = []
        for metric in validation_metrics:
            rows.append(
                f"| {metric.get('parameter_id', '?')} | "
                f"{metric.get('validation_method', '')} | "
                f"{metric.get('metric_name', '')} | "
                f"{metric.get('metric_value', '')} | "
                f"{metric.get('threshold', '')} | "
                f"{metric.get('status', '')} |"
            )
        
        if not rows:
            rows.append(f"| {' | '.join([self.MISSING_DATA] * len(headers))} |")
        
        content.extend([header_row, separator] + rows)
        return "\n".join(content)