# src/model_intermediate/structures.py

from typing import Dict, List, Any, Optional

class BaseModel:
    """Classe de base pour toutes les entités du Modèle Intermédiaire."""
    def __init__(self, id: str, name: str, description: str = "", **kwargs):
        self.id = id
        self.name = name
        self.description = description
        # Stocke les autres attributs extraits du XMI non explicitement mappés
        self.xmi_data = kwargs 

class PropertyModel(BaseModel):
    """Représente une Resource ou un Parameter (issue du XMI)."""
    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(id, name, **kwargs)
        # Attributs clés pour la transformation
        self.emf_type: str = kwargs.pop('emf_type', 'Property') # Resource ou Parameter
        self.unit: Optional[str] = kwargs.pop('unit', None)
        self.value: Optional[Any] = kwargs.pop('value', None) # Valeur du XMI ou du JSON

        # Relation (référence d'ID)
        self.heldBy_refs: List[str] = kwargs.pop('heldBy_refs', [])

class ProcessModel(BaseModel):
    """Représente un Processus (Transformation ou Movement) (issue du XMI)."""
    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(id, name, **kwargs)
        # Attributs clés pour la transformation GAML
        self.emf_type: str = kwargs.pop('emf_type', 'Process') # TProcess ou MProcess
        self.pseudoCode: Optional[str] = kwargs.pop('pseudoCode', None)
        self.equation: Optional[str] = kwargs.pop('equation', None)
        self.source: Optional[str] = kwargs.pop('source', None)
        self.destination: Optional[str] = kwargs.pop('destination', None)

        # Relations (Références d'IDs)
        self.subjects_refs: List[str] = kwargs.pop('subjects_refs', [])
        self.involvedResources_refs: List[str] = kwargs.pop('involvedResources_refs', [])
        self.affectsResources_refs: List[str] = kwargs.pop('affectsResources_refs', [])

        # ATTRIBUTS FUSIONNÉS (via JSON)
        self.trigger_condition: Optional[str] = None # 'Quand' le processus s'exécute

class AgentModel(BaseModel):
    """Représente un Agent (Agent Ecore) qui deviendra une Species GAML."""
    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(id, name, **kwargs)
        # Attributs clés de position/forme
        self.pos_x: Optional[float] = kwargs.pop('pos_x', None)
        self.pos_y: Optional[float] = kwargs.pop('pos_y', None)
        self.width: Optional[float] = kwargs.pop('width', None)
        self.height: Optional[float] = kwargs.pop('height', None)
        self.partOfParentAgent_ref: Optional[str] = kwargs.pop('partOfParentAgent_ref', None) # Héritage potentiel

        # AGGRÉGATIONS FINALES (Ressources et Processus convertis)
        # Ces attributs contiennent des objets ProcessModel ou PropertyModel
        self.attributes: List[PropertyModel] = [] # Resources + Parameters locaux
        # self.actions: List[ProcessModel] = []

        # ATTRIBUTS FUSIONNÉS (via JSON)
        self.initial_count: Optional[int] = 0
        self.initialization_method: Optional[str] = None
        
        # Le code Jinja2 aura besoin de savoir si cet agent est le parent d'un autre
        self.is_parent: bool = False 
        


class SocioEcosystemModel:
    """
    Conteneur racine du Modèle Intermédiaire. 
    Il agrège toutes les entités et les données globales du JSON.
    """
    def __init__(self):
        # Entités principales du XMI (mappées en ID pour la recherche rapide)
        self.agents: Dict[str, AgentModel] = {}
        self.properties: Dict[str, PropertyModel] = {}
        self.processes: Dict[str, ProcessModel] = {}
        
        # Données globales extraites des JSON/YAML
        self.global_parameters: List[Dict] = []
        self.initialization_config: Dict[str, Any] = {}
        self.indicators: List[Dict] = []
        self.scenarios: List[Dict] = []
        
        # Optionnel : Stockage de metadata contextuels
        self.metadata: Dict[str, Any] = {}  # Pour introduction/user_manual si besoin

    def get_agent_by_id(self, agent_id: str) -> Optional[AgentModel]:
        """Fonction utilitaire pour retrouver un agent par son ID."""
        return self.agents.get(agent_id)

    def get_property_by_id(self, prop_id: str) -> Optional[PropertyModel]:
        """Fonction utilitaire pour retrouver une propriété par son ID."""
        return self.properties.get(prop_id)