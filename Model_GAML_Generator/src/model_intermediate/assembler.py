# src/model_intermediate/assembler.py

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Importation des structures définies en I.2
from .structures import SocioEcosystemModel, AgentModel, PropertyModel, ProcessModel
# Importation du parser XMI (raffiné)
from ..parsers.xmi_parser import XMIParser
# Importation des loaders spécialisés (raffinés)
from ..loaders.generic_yaml_json_loader import load_introduction_data, load_user_manual_data
from ..loaders.indicator_loader import load_indicator_data
from ..loaders.initialization_loader import load_initialization_data 

logger = logging.getLogger(__name__)

class AssemblerError(Exception):
    """Exception custom pour erreurs d'assemblage."""
    pass

class ModelAssembler:
    """
    Assemble le modèle intermédiaire (M') en fusionnant:
    1. Les données structurelles et comportementales (XMI).
    2. Les données d'initialisation et de contexte (YAML/JSON, CSV/Multi-CSV).
    """
    def __init__(self, xmi_path: str, input_dir: str, strict_mode: bool = False):
        self.xmi_parser = XMIParser(xmi_path)
        self.input_dir = input_dir 
        self.model = SocioEcosystemModel()
        self.xmi_data: Dict[str, Any] = {}
        self.json_data: Dict[str, Any] = {} 
        self.warning_count = 0  # Compteur pour summary
        self.strict_mode = strict_mode  # Nouveau

    def assemble(self) -> SocioEcosystemModel:
        """Exécute l'extraction, l'instanciation et la fusion."""
        logger.info("--- PHASE I.4: Démarrage de l'Assemblage du Modèle Intermédiaire ---")
        
        logger.info("1. Extraction des données brutes (XMI et Sources Externes)...")
        self.xmi_data = self.xmi_parser.parse_model()
        self._load_all_external_data()
        
        # Phase 1: Instanciation de toutes les entités de base (XMI)
        logger.info("2. Instanciation des entités de base...")
        self._instantiate_base_entities()

        # Phase 2: Rétablissement des relations sémantiques (XMI)
        logger.info("3. Rétablissement des liens sémantiques...")
        self._link_properties_to_agents()
        self._link_processes_to_agents()
        self._link_agent_hierarchy()

        # Phase 3: Fusion des données externes (JSON/CSV)
        logger.info("4. Fusion des données d'initialisation et des indicateurs (JSON/CSV)...")
        self._merge_global_data()
        self._merge_agent_initialization()
        self._merge_indicators()
        
        self._validate_model()
        
        # Summary UX
        logger.info(f"--- Assemblage du Modèle Intermédiaire (M') terminé. Summary : {len(self.model.agents)} agents fusionnés, {self.warning_count} warnings (voir détails ci-dessus). ---")
        return self.model

    def _load_all_external_data(self):
        """Coordonne l'appel de tous les loaders spécialisés."""
        try:
            self.json_data['introduction'] = load_introduction_data(self.input_dir)
            self.json_data['user_manual'] = load_user_manual_data(self.input_dir)
            self.json_data['indicators'] = load_indicator_data(self.input_dir)
            self.json_data['initialization'] = load_initialization_data(self.input_dir)
            
            # === ÉTAPE 3 : VALIDATIONS DYNAMIQUES (AJOUT ICI) ===
            # Comparaison des noms d'entités JSON vs XMI
            xmi_agent_names = {agent.get('name', '').lower() for agent in self.xmi_data.get('agents', [])}
            json_entity_names = {
                entity.get('name', '').lower()
                for entity in self.json_data.get('initialization', {}).get('entities', [])
            }
            
            mismatches = json_entity_names - xmi_agent_names
            if mismatches:
                logger.warning(
                    f"Mismatch noms entités JSON vs XMI : {sorted(mismatches)}. "
                    f"Vérifiez l'orthographe ou la casse dans initialization.yml. "
                    f"Noms disponibles dans XMI : [{', '.join(sorted(xmi_agent_names))}]. "
                    f"Les entités manquantes seront créées comme placeholders lors de la fusion."
                )
                self.warning_count += len(mismatches)
            
            # Optionnel : Mode strict (à activer via __init__ si besoin)
            if hasattr(self, 'strict_mode') and self.strict_mode and self.warning_count > 0:
                raise AssemblerError(
                    f"Mode strict activé : {self.warning_count} problème(s) détecté(s) lors du chargement. "
                    "Corrigez les mismatches avant de continuer."
                )
            # ================================================

            # Fusion dans le modèle (inchangée)
            self.model.metadata['introduction'] = self.json_data['introduction']
            self.model.metadata['user_manual'] = self.json_data['user_manual']
            
            self.model.scenarios = self.json_data['initialization'].get('scenarios', [])
        except Exception as e:
            logger.error(f"Erreur lors du loading des données externes: {e}")
            raise AssemblerError("Échec du loading des sources externes.") from e

    def _instantiate_base_entities(self):
        """Instancie les objets Python à partir des données XMI brutes."""
        for prop_data in self.xmi_data.get('properties', []):
            prop_id = prop_data.pop('id')
            self.model.properties[prop_id] = PropertyModel(id=prop_id, **prop_data)
        
        for agent_data in self.xmi_data.get('agents', []):
            agent_id = agent_data.pop('id')
            self.model.agents[agent_id] = AgentModel(id=agent_id, **agent_data)
        
        for proc_data in self.xmi_data.get('processes', []):
            proc_id = proc_data.pop('id')
            self.model.processes[proc_id] = ProcessModel(id=proc_id, **proc_data)

    def _link_properties_to_agents(self):
        """Associe les Properties (Resources) à leurs Agents conteneurs (heldBy)."""
        unresolved = []
        for prop_id, prop_obj in self.model.properties.items():
            for agent_ref in prop_obj.heldBy_refs:
                agent_obj = self.model.get_agent_by_id(agent_ref)
                if agent_obj:
                    agent_obj.attributes.append(prop_obj)
                else:
                    unresolved.append(agent_ref)
                    self.warning_count += 1
        if unresolved:
            logger.warning(f"Agents non résolus pour properties: {unresolved}")

    def _link_processes_to_agents(self):
        """Associe les Processus à leurs Agents sujets (subjects)."""
        unresolved = []
        for proc_id, proc_obj in self.model.processes.items():
            for agent_ref in proc_obj.subjects_refs:
                agent_obj = self.model.get_agent_by_id(agent_ref)
                if agent_obj:
                    pass
                else:
                    unresolved.append(agent_ref)
                    self.warning_count += 1
        if unresolved:
            logger.warning(f"Agents non résolus pour processes: {unresolved}")

    def _link_agent_hierarchy(self):
        """Gère l'héritage entre Agents (partOfParentAgent)."""
        for agent_id, agent_obj in self.model.agents.items():
            if agent_obj.partOfParentAgent_ref:
                parent_obj = self.model.get_agent_by_id(agent_obj.partOfParentAgent_ref)
                if parent_obj:
                    parent_obj.is_parent = True
                else:
                    logger.warning(f"Parent non résolu pour agent {agent_id}: {agent_obj.partOfParentAgent_ref}")
                    self.warning_count += 1

    def _get_json_global_params_values(self) -> Dict[str, Any]:
        """Consolide les valeurs des paramètres globaux provenant des sources JSON (Priorité 2)."""
        logger.info("  -> Début de la consolidation des valeurs de paramètres globaux depuis le JSON/Indicators.")
        json_global_values: Dict[str, Any] = {}
        init_data = self.json_data.get('initialization', {})
        indicators_data = self.json_data.get('indicators', [])
        
        # 1. Depuis initialization.yml
        init_params = init_data.get('parameters', {}).get('definitions', [])
        logger.debug(f"     -> {len(init_params)} paramètres trouvés dans 'initialization.parameters.definitions'.")
        for p in init_params:
            if p.get('name'):
                param_key = p['name'].lower().replace(' ', '_')
                json_global_values[param_key] = p.get('value')
                logger.debug(f"     -> JSON Init: '{p['name']}' ({param_key}) mis à jour avec la valeur: {p.get('value')}")
        
        # 2. Depuis indicators.json (si 'entity'='Système')
        for ind in indicators_data:
            for param in ind.get('parameters', []):
                if param.get('entity', '').lower() == 'système' and param.get('name'):
                    param_key = param['name'].lower().replace(' ', '_')
                    json_global_values[param_key] = param.get('value')
                    logger.debug(f"     -> JSON Indicator: '{param['name']}' ({param_key}) mis à jour avec la valeur: {param.get('value')}")

        logger.info(f"  -> Consolidation JSON terminée. {len(json_global_values)} entrées de paramètres JSON capturées.")
        return json_global_values

    def _merge_global_data(self):
        """
        Finalise la configuration globale et fusionne les paramètres globaux (XMI > JSON).
        """
        # a) Récupérer les valeurs JSON (Priorité 2)
        init_data = self.json_data.get('initialization', {})
        
        # --- Part 1: Configuration Spatiale et Temporelle (Non modifiée) ---
        global_config = init_data.get('global', {})
        self.model.initialization_config['temporal'] = global_config.get('temporal_scope', {'time_step': '1 day'})
        self.model.initialization_config['spatial'] = global_config.get('spatial_configuration', {})
        if not global_config.get('temporal_scope'):
            logger.warning("Configuration temporelle absente, fallback à time_step='1 day'.")
        
        # --- Part 2: Fusion des Paramètres Globaux ---
        logger.info("  -> Début de la fusion des paramètres globaux XMI avec les valeurs JSON.")
        
        # a) Récupérer les valeurs JSON (Priorité 2)
        json_global_values = self._get_json_global_params_values()
        
        final_global_params_list = []
        
        # Compteur pour le débogage
        properties_total = len(self.model.properties)
        logger.debug(f"     -> Total de PropertyModel à inspecter: {properties_total}")

        # On itère sur les PropertyModel restants dans le dictionnaire
        for prop_id, prop_obj in list(self.model.properties.items()): 
            
            # Condition pour identifier un paramètre global XMI
            is_global_param = prop_obj.emf_type == 'Parameter' and not prop_obj.heldBy_refs
            
            if is_global_param:
                prop_name_normalized = prop_obj.name.lower().replace(' ', '_')
                
                # Priorité 1: Valeur XMI (déjà dans prop_obj.value si le parser l'a trouvée)
                final_value = prop_obj.value
                
                # Priorité 2: Valeur JSON (si XMI est absent)
                json_value = json_global_values.get(prop_name_normalized)
                
                # LOGGING DÉTAILLÉ
                logger.debug(f"     -> Traitement du Paramètre XMI: '{prop_obj.name}' (ID: {prop_id})")
                logger.debug(f"        -> XMI value (P1): {final_value}")
                logger.debug(f"        -> JSON value (P2): {json_value}")
                
                source_used = "XMI" # Par défaut, si non None
                if final_value is None and json_value is not None:
                    final_value = json_value
                    source_used = "JSON"
                elif final_value is None and json_value is None:
                    # Règle de Défaut: 0.0 si numérique, sinon None/chaîne vide
                    # Si vous souhaitez forcer 0.0 ici si c'est une unité numérique :
                    if prop_obj.unit in ['float', 'int'] or not prop_obj.unit: # Ajout du test sur l'unité pour la valeur par défaut
                        final_value = 0.0
                    else:
                        final_value = None
                    source_used = "Default (0.0/None)"

                if isinstance(final_value, str):
                    try:
                        # Tente de convertir la chaîne en float si elle ressemble à un nombre
                        converted_value = float(final_value)
                        final_value = converted_value
                    except ValueError:
                        # Garde la chaîne si la conversion échoue (ex: 'formula_A')
                        pass
                
                # Mise à jour de l'objet PropertyModel
                prop_obj.value = final_value
                
                # Préparation du format attendu par le GAML Generator (liste de dicts)
                param_data = {
                    'name': prop_obj.name,
                    'unit': prop_obj.unit,
                    'value': final_value,
                    # Assurez-vous que xmi_data est correct si la propriété 'definition' n'est pas au niveau racine
                    'definition': prop_obj.xmi_data.get('definition', prop_obj.description) or '', 
                    'id': prop_obj.id
                }
                final_global_params_list.append(param_data)
                
                logger.debug(f"        -> Valeur Finale: {final_value} (Source: {source_used})")
                
                # Retirer de self.model.properties car ils sont désormais des global_parameters
                del self.model.properties[prop_id]

            else:
                logger.debug(f"     -> Propriété ignorée: '{prop_obj.name}' (ID: {prop_id}, Type: {prop_obj.emf_type}). N'est pas un paramètre global.")

        self.model.global_parameters = final_global_params_list
        logger.info(f"  -> Fusion terminée. Paramètres globaux XMI fusionnés et finalisés: {len(self.model.global_parameters)} trouvés.")

    def _merge_agent_initialization(self):
        """Applique les valeurs d'initialisation et le nombre d'agents aux objets AgentModel."""
        init_data = self.json_data.get('initialization', {})
        xmi_agent_names = {agent.name.lower() for agent in self.model.agents.values()}
        
        # 1. Initialisation des attributs des Agents (State Variables)
        for sv in init_data.get('state_variables', {}).get('definitions', []):
            entity_name = sv.get('entity')
            variable_name = sv.get('name')
            initial_value = sv.get('initial_value')

            # Case-insensitive recherche
            agent_found: AgentModel = next(
                (a for a in self.model.agents.values() if a.name.lower() == entity_name.lower()), None
            )
            if agent_found:
                attr_found: PropertyModel = next(
                    (attr for attr in agent_found.attributes if attr.name.lower() == variable_name.lower()), None
                )
                if attr_found:
                    if attr_found.value is None or str(attr_found.value).strip() == '':
                        attr_found.value = initial_value
                    # Logique : Si XMI a une valeur, on la garde. Sinon on prend la valeur JSON.
                else:
                    logger.warning(
                        f"Attribut non trouvé pour {entity_name}: {variable_name}. Attributs disponibles : "
                        f"[{', '.join(attr.name for attr in agent_found.attributes)}]"
                    )
                    self.warning_count += 1
            else:
                logger.warning(
                    f"Agent non trouvé pour state_variable: {entity_name}. Agents disponibles (XMI) : "
                    f"[{', '.join(sorted(xmi_agent_names))}] - vérifiez case ou ajoutez en XMI."
                )
                self.warning_count += 1

        # 2. Initialisation du nombre d'Agents (Entities)
        for entity in init_data.get('entities', []):
            agent_name = entity.get('name')
            initial_count = entity.get('initial_count')
            
            agent_found: AgentModel = next(
                (a for a in self.model.agents.values() if a.name.lower() == agent_name.lower()), None
            )
            if agent_found and initial_count:
                # CORRECTION (XMI > JSON): N'écraser le count XMI (agent_found.initial_count) que si il est ABSENT (None).
                if agent_found.initial_count is None:
                    try:
                        agent_found.initial_count = int(initial_count)
                    except ValueError:
                        logger.warning(f"Valeur initial_count invalide pour {agent_name}: {initial_count} - fallback à 1")
                        agent_found.initial_count = 1 # 1 est un meilleur défaut que 0 pour un agent GAMA
                        self.warning_count += 1
                # Sinon (si XMI a une valeur), agent_found.initial_count conserve la valeur XMI.
            elif not agent_found:
                # Créer placeholder
                placeholder_id = f"placeholder_{agent_name}_{len(self.model.agents)}"
                self.model.agents[placeholder_id] = AgentModel(
                    id=placeholder_id, name=agent_name, description="Placeholder pour entité JSON manquante"
                )
                try:
                    self.model.agents[placeholder_id].initial_count = int(initial_count) if initial_count else 0
                except ValueError:
                    logger.warning(f"Valeur initial_count invalide pour placeholder {agent_name}: {initial_count} - fallback à 0")
                    self.model.agents[placeholder_id].initial_count = 0
                logger.warning(
                    f"Agent non trouvé pour entity: {agent_name}. Placeholder créé (ID={placeholder_id}). "
                    f"Agents disponibles (XMI) : [{', '.join(sorted(xmi_agent_names))}]"
                )
                self.warning_count += 1

    def _merge_indicators(self):
        """Copie la liste d'indicateurs du Loader Indicateurs vers le modèle."""
        self.model.indicators = self.json_data.get('indicators', [])


    def _validate_model(self):
        """Valide l'intégrité du modèle assemblé."""
        if not self.model.agents:
            raise AssemblerError(
                "Aucun agent dans le modèle assemblé – vérifiez votre fichier XMI."
            )
        
        # ... (Vérification des références non résolues)
        unresolved_refs = [
            ref for agent in self.model.agents.values()
            for ref in (agent.partOfParentAgent_ref,) if ref and ref not in self.model.agents
        ]
        if unresolved_refs:
            logger.warning(f"Références non résolues dans hierarchy: {unresolved_refs}")
            self.warning_count += 1
        
        # Identification des agents liés à un Processus
        agents_with_processes = set()
        for process in self.model.processes.values():
            for agent_id in process.subjects_refs:
                agents_with_processes.add(agent_id)

        # Vérifier si l'agent a des attributs OU est le sujet d'un processus
        empty_agents = [
            a.name for a in self.model.agents.values() 
            if not a.attributes and a.id not in agents_with_processes
        ]
        
        if empty_agents:
            logger.warning(
                f"Agents sans attributes/processus: {empty_agents} - vérifiez les liens heldBy/subjects dans XMI."
            )
            self.warning_count += 1