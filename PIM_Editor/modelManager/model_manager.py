"""
Gestionnaire de modèle Ecore pour l'éditeur graphique SocioEcosystem.
Gère la création, le chargement, la sauvegarde et les opérations sur le modèle.
"""
import sys
from pathlib import Path
from pyecore.ecore import *
from pyecore.resources import ResourceSet, URI
from lxml.etree import parse 
import uuid
import tempfile 
import os 
from PySide6.QtCore import QPointF

# Configuration du path pour les modules locaux
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from xml_resource import XMLResource
from xml_serializer import serialize_to_xmi


class ModelManager:
    """
    Gestionnaire principal du modèle Ecore pour l'éditeur SocioEcosystem.
    
    Responsabilités :
    - Chargement du métamodèle
    - Création/sauvegarde/ouverture des modèles
    - Gestion des éléments (Agents, Resources, Processes, etc.)
    - Gestion des connecteurs et relations
    - Validation des connexions
    """
    
    def __init__(self, metamodel_path):
        """
        Initialise le gestionnaire de modèle.
        
        Args:
            metamodel_path (str): Chemin vers le fichier Ecore du métamodèle
        """
        self.rset = ResourceSet()
        #self.rset.resource_factory['xmi'] = lambda uri: XMLResource(uri)

        self.resource = None
        self.metamodel_path = metamodel_path
        self.mm_root = None
        self.current_model = None
        self.current_file = None
        self.socioecosystem = None
        
        # Dictionnaires pour la gestion des connecteurs
        self.connector_labels = {}
        self.control_points = {}
        self.connector_types = {}
        
        # Références vers les classes Ecore
        self._ecore_classes = {}
        
        self._load_metamodel()

    def _load_metamodel(self):
        """
        Charge le métamodèle Ecore et initialise les références de classes.
        """
        try:
            ecore_resource = self.rset.get_resource(URI(self.metamodel_path))
            self.mm_root = ecore_resource.contents[0]
            self.rset.metamodel_registry[self.mm_root.nsURI] = self.mm_root
            
            # Initialisation des classes Ecore
            self._initialize_ecore_classes()
            self._configure_id_attributes()
            
        except Exception as e:
            print(f"Erreur lors du chargement du métamodèle: {e}")
            raise

    def _initialize_ecore_classes(self):
        """
        Initialise les références vers TOUTES les classes Ecore du métamodèle.
        """
        class_names = [
            'SocioEcosystem', 'Agent', 'Resource', 'Process', 
            'Property', 'Parameter', 'TransformationProcess', 'MovementProcess',
            'AgentType', 'TransformationType'  # Les enums aussi !
        ]
        
        for class_name in class_names:
            eclass = self.mm_root.getEClassifier(class_name)
            if eclass:
                self._ecore_classes[class_name] = eclass
            else:
                print(f"ATTENTION: Classe {class_name} non trouvée dans le métamodèle")

    def _configure_id_attributes(self):
        """
        Configure les attributs ID pour les classes Ecore.
        """
        for class_name in ['Agent', 'Resource', 'Process', 'Property', 'Parameter']:
            eclass = self._ecore_classes.get(class_name)
            if eclass:
                id_feature = self._find_structural_feature(eclass, 'id')
                if id_feature:
                    eclass.eIDAttribute = id_feature

    def _find_structural_feature(self, eclass, feature_name):
        """
        Trouve un feature structurel par nom dans une classe Ecore.
        
        Args:
            eclass: Classe Ecore
            feature_name (str): Nom du feature recherché
            
        Returns:
            Feature structurel ou None si non trouvé
        """
        for feature in eclass.eStructuralFeatures:
            if feature.name == feature_name:
                return feature
        return None

    # === Gestion des modèles ===

    def new_model(self, filename):
        """
        Crée un nouveau modèle SocioEcosystem.
        
        Args:
            filename (str): Chemin du fichier pour sauvegarder le modèle
        """
        try:
            self.current_model = self._ecore_classes['SocioEcosystem'](
                name="Nouveau Socio-Écosystème",
                description="Modèle créé avec l'éditeur MDD"
            )
            self.socioecosystem = self.current_model
            self.resource = XMLResource(URI(filename))
            self.resource.append(self.current_model)
            self.current_file = filename

            # Réinitialisation des connecteurs
            self.connector_labels.clear()
            self.control_points.clear()
            self.connector_types.clear()
            
            # Stabilisation des collections
            self._stabilize_model_collections()
            
            self.save_model()
            
        except Exception as e:
            print(f"Erreur lors de la création du nouveau modèle: {e}")
            raise

    # ---------------------------------------------------------------------------------------------------
    def open_model(self, filename):
        """
        Ouvre un modèle existant depuis un fichier.
        """
        # Agent - Process
        is_subject_of_ref = None
        is_object_of_ref = None
        subjects_ref = None
        objects_ref = None
        original_opposite_iso = None
        original_opposite_ioo = None
        original_opposite_sub = None
        original_opposite_obj = None
        
        # Agent - Agent
        contains_agents_ref = None
        part_of_parent_agent_ref = None
        original_opposite_ca = None
        original_opposite_popa = None

        # Agent - Resource
        holdReources_ref = None
        heldBy_ref = None
        original_opposite_hr = None
        original_opposite_hb = None
        
        try:
            # 1. ROMPRE LE LIEN OPPOSÉ AVANT LE CHARGEMENT
            (contains_agents_ref, part_of_parent_agent_ref, 
            holdReources_ref, heldBy_ref,
            is_subject_of_ref, is_object_of_ref,
            subjects_ref, objects_ref) = self._get_agent_references()
            
            # Sauvegarder les références originales
            original_opposite_ca = contains_agents_ref.eOpposite
            original_opposite_popa = part_of_parent_agent_ref.eOpposite
            original_opposite_hr = holdReources_ref.eOpposite
            original_opposite_hb = heldBy_ref.eOpposite
            original_opposite_iso = is_subject_of_ref.eOpposite
            original_opposite_ioo = is_object_of_ref.eOpposite
            original_opposite_sub = subjects_ref.eOpposite
            original_opposite_obj = objects_ref.eOpposite
            
            # Rompre le lien dans le métamodèle pour le chargeur
            contains_agents_ref.eOpposite = None
            part_of_parent_agent_ref.eOpposite = None
            holdReources_ref.eOpposite = None
            heldBy_ref.eOpposite = None
            is_subject_of_ref.eOpposite = None
            is_object_of_ref.eOpposite = None
            subjects_ref.eOpposite = None
            objects_ref.eOpposite = None
            
            load_options = {
                'xmi:resolve': True,
                'xmi:opposite': False,
                'xmi:containment': True,
                'xmi:defer-resolution': True
            }

            self.resource = self.rset.get_resource(URI(filename))
            self.resource.load(options=load_options)

            if len(self.resource.contents) > 0:
                self.current_model = self.resource.contents[0]
                self.socioecosystem = self.current_model

                while len(self.resource.contents) > 1:
                    self.resource.contents.pop()
            else:
                raise ValueError("Aucun modèle trouvé dans le fichier")

            self.current_file = filename

            # Chargement des connecteurs
            (self.connector_labels, 
            self.control_points, 
            self.connector_types) = self._load_connector_labels(filename)

            # 3. RÉSOLUTION MANUELLE (Recréer les liens de l'opposé qui ont été sautés)
            self._resolve_opposites() 

            # 4. RESTAURER LE LIEN OPPOSÉ
            if original_opposite_ca is not None:
                contains_agents_ref.eOpposite = original_opposite_ca
            if original_opposite_popa is not None:
                part_of_parent_agent_ref.eOpposite = original_opposite_popa
            if original_opposite_hr is not None:
                holdReources_ref.eOpposite = original_opposite_hr
            if original_opposite_hb is not None:
                heldBy_ref.eOpposite = original_opposite_hb
            if original_opposite_iso is not None:
                is_subject_of_ref.eOpposite = original_opposite_iso
            if original_opposite_ioo is not None:
                is_object_of_ref.eOpposite = original_opposite_ioo
            if original_opposite_sub is not None:
                subjects_ref.eOpposite = original_opposite_sub
            if original_opposite_obj is not None:
                objects_ref.eOpposite = original_opposite_obj

            return self.current_model

        except Exception as e:
            print(f"Erreur lors de l'ouverture du modèle : {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # GARANTIR LA RESTAURATION même en cas d'échec de load()
            if contains_agents_ref and original_opposite_ca is not None and contains_agents_ref.eOpposite is None:
                contains_agents_ref.eOpposite = original_opposite_ca
            if part_of_parent_agent_ref and original_opposite_popa is not None and part_of_parent_agent_ref.eOpposite is None:
                part_of_parent_agent_ref.eOpposite = original_opposite_popa
            if holdReources_ref and original_opposite_hr is not None and holdReources_ref.eOpposite is None:
                holdReources_ref.eOpposite = original_opposite_hr
            if heldBy_ref and original_opposite_hb is not None and heldBy_ref.eOpposite is None:
                heldBy_ref.eOpposite = original_opposite_hb
            if is_subject_of_ref and original_opposite_iso is not None and is_subject_of_ref.eOpposite is None:
                is_subject_of_ref.eOpposite = original_opposite_iso
            if is_object_of_ref and original_opposite_ioo is not None and is_object_of_ref.eOpposite is None:
                is_object_of_ref.eOpposite = original_opposite_ioo
            if subjects_ref and original_opposite_sub is not None and subjects_ref.eOpposite is None:
                subjects_ref.eOpposite = original_opposite_sub
            if objects_ref and original_opposite_obj is not None and objects_ref.eOpposite is None:
                objects_ref.eOpposite = original_opposite_obj 

    def _resolve_opposites(self):
        """
        Résout manuellement les relations bidirectionnelles après le chargement.
        """
        if not self.current_model:
            return

        all_agents = list(self.current_model.agents)
        all_resources = [p for p in self.current_model.properties 
                        if isinstance(p, self._ecore_classes['Resource'])]
        all_processes = list(self.current_model.processes)
        
        # Récupérer tous les objets EReference
        try:
            (contains_agents_ref, part_of_parent_agent_ref, 
            holdReources_ref, heldBy_ref,
            is_subject_of_ref, is_object_of_ref,
            subjects_ref, objects_ref) = self._get_agent_references()
        except RuntimeError:
            print("ATTENTION: Impossible de récupérer les EReferences pour la résolution manuelle.")
            return

        # Résolution des relations Agent-Agent (existantes)
        for agent in all_agents:
            for contained in list(agent.containsAgents):
                if contained.partOfParentAgent != agent: 
                    contained.eSet(part_of_parent_agent_ref, agent)
                    if contained.partOfParentAgent == agent:
                        print(f"Résolu [partOfParentAgent]: {contained.id}'s parent est {agent.id}")

        # Résolution des relations Agent-Resource (existantes)
        for agent in all_agents:
            for hold in list(agent.holdsResources):
                if hold.heldBy != agent: 
                    hold.eSet(heldBy_ref, agent)
                    if hold.heldBy == agent:
                        print(f"Résolu [heldBy]: {hold.id}'s agent est {agent.id}")

        # Résolution des relations Agent-Process (isSubjectOf/subjects)
        for agent in all_agents:
            for process in list(agent.isSubjectOf):
                # Vérifier si le Process a cet Agent dans ses subjects
                if process.subjects != agent:
                    process.eSet(subjects_ref, agent)
                    if process.subjects == agent:
                        print(f"Résolu [subjects]: {process.id} a maintenant {agent.id} comme sujet")
        
        # Résolution des relations Agent-Process (isObjectOf/objects)
        for agent in all_agents:
            for process in list(agent.isObjectOf):
                # Vérifier si le Process a cet Agent dans ses objects
                if hasattr(process, 'objects') and agent not in process.objects:
                    process.objects.append(agent)
                    print(f"Résolu [objects]: {process.id} a maintenant {agent.id} comme objet")

        '''
        # Résolution inverse (Process → Agent)
        for process in all_processes:
            # Résolution subjects
            agent = process.subjects
            if process not in agent.isSubjectOf:
                agent.isSubjectOf.append(process)
                print(f"Résolu [isSubjectOf]: {agent.id} est maintenant sujet de {process.id}")
            
            # Résolution objects
            if hasattr(process, 'objects'):
                for agent in list(process.objects):
                    if process not in agent.isObjectOf:
                        agent.isObjectOf.append(process)
                        print(f"Résolu [isObjectOf]: {agent.id} est maintenant objet de {process.id}")
        '''
        
                        

    def _get_agent_references(self):
        """
        Récupère les objets EReference problématiques depuis l'Ecore.
        """
        package_uri = 'http://www.example.org/socioecosystem.en'
        
        if package_uri not in self.rset.metamodel_registry:
            raise RuntimeError(f"Le package Ecore '{package_uri}' n'est pas enregistré dans le ResourceSet.")
            
        socio_package = self.rset.metamodel_registry[package_uri] 
        agent_class = socio_package.getEClassifier('Agent')
        resource_class = socio_package.getEClassifier('Resource')
        process_class = socio_package.getEClassifier('Process')
        
        if not agent_class:
            raise RuntimeError("La classe 'Agent' est introuvable dans le package SocioEcosystem.")
        
        # Références pour les relations Agent-Process
        is_subject_of_ref = agent_class.findEStructuralFeature('isSubjectOf')
        is_object_of_ref = agent_class.findEStructuralFeature('isObjectOf')
        subjects_ref = process_class.findEStructuralFeature('subjects')
        objects_ref = process_class.findEStructuralFeature('objects')
        
        # Références pour les relations Agent-Agent
        contains_agents_ref = agent_class.findEStructuralFeature('containsAgents')
        part_of_parent_agent_ref = agent_class.findEStructuralFeature('partOfParentAgent')
        
        # Références pour les relations Agent-Resourve
        holdReources_ref = agent_class.findEStructuralFeature('holdsResources')
        heldBy_ref = resource_class.findEStructuralFeature('heldBy')
        
        if not contains_agents_ref or not part_of_parent_agent_ref:
            raise RuntimeError("Les références 'containsAgents' ou 'partOfParentAgent' sont introuvables.")
        
        # RETOURNER les nouvelles références
        return (contains_agents_ref, part_of_parent_agent_ref, 
                holdReources_ref, heldBy_ref,
                is_subject_of_ref, is_object_of_ref,
                subjects_ref, objects_ref)
    # ---------------------------------------------------------------------------------------------------


    def _stabilize_model_collections(self):
        """
        Stabilise les collections du modèle et force la résolution de tous les proxies.
        Rend le chargement robuste à l'ordre des éléments dans le fichier XMI.
        """
        if not self.current_model:
            return
            
        root = self.current_model
        
        # 1. Stabilisation des collections RACINES (Bonne pratique)
        features_to_stabilize = ['agents', 'processes', 'properties']
        
        for feature_name in features_to_stabilize:
            if hasattr(root, feature_name):
                try:
                    # La conversion en list() force l'accès et donc la résolution des proxies racines
                    collection = getattr(root, feature_name)
                    resolved_list = list(collection) 
                    setattr(root, feature_name, resolved_list)
                except Exception as e:
                    # Capture l'erreur si un proxy dans la liste racine n'a pas pu être résolu
                    print(f"DEBUG: Échec stabilisation collection racine '{feature_name}': {e}")
                    
        # 2. Résolution des proxies dans les références croisées internes
        # Parcourir TOUS les éléments du modèle, y compris les éléments contenus
        
        all_elements = root.eAllContents()
        
        for element in all_elements:
            for ref in element.eClass.eAllReferences():
                # Exclure les références de containment et les références techniques inverses
                if ref.containment or ref.name in ['partOfParentAgent', 'heldBy']:
                    continue
                    
                try:
                    # Accéder à la référence force la résolution du proxy PyEcore
                    # Pour les listes (upperBound="-1")
                    if ref.many:
                        # Accéder à la liste force la résolution de tous ses membres
                        _ = list(element.eGet(ref.name))
                        
                    # Pour les références simples (upperBound="1" ou non défini)
                    else:
                        # L'accès seul force la résolution (la valeur retournée sera l'objet résolu ou None)
                        resolved_target = element.eGet(ref.name)
                        # Si l'objet résolu est un proxy, l'accès ci-dessus le déclenche.
                        
                except Exception as e:
                    # Si le proxy ne peut pas être résolu (ID manquant), cela sera capturé ici
                    target_id = None
                    try:
                        # Tenter d'afficher l'ID du proxy qui a échoué (utile pour le débogage)
                        target_id = element.eGet(ref.name).uriFragment
                    except:
                        pass
                    
                    print(f"ERREUR PROXY: Échec de résolution pour {element.eClass.name}.{ref.name} -> {target_id}. {e}")


    def save_model(self, filename=None):
        """
        Sauvegarde le modèle courant.
        
        Args:
            filename (str): Chemin de sauvegarde (utilise current_file si None)
        """
        if not filename:
            filename = self.current_file
            
        if not self.current_model:
            print("Erreur : Aucun modèle à sauvegarder.")
            return
            
        try:
            serialize_to_xmi(
                self.current_model, filename, self, 
                self.connector_labels, self.control_points, self.connector_types
            )
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {e}")
            raise

    # === Création d'éléments ===

    def create_agent(self, data, add_to_model=False):
        """
        Crée un nouvel Agent dans le modèle.
        
        Args:
            data (dict): Données de l'agent
            
        Returns:
            L'agent créé ou None en cas d'erreur
        """
        if not self.current_model:
            return None
        
        try:
            #agent_type_enum = self._ecore_classes['AgentType'].getEEnumLiteral(data.get("type", "Human"))
            agent_type = data.get("type")
        
            # Si c'est un string, le convertir en enum
            if isinstance(agent_type, str):
                agent_type_enum = self._ecore_classes['AgentType'].getEEnumLiteral(agent_type)
                if not agent_type_enum:
                    agent_type_enum = self._ecore_classes['AgentType'].getEEnumLiteral("Human")
            else:
                # C'est déjà un enum literal
                agent_type_enum = agent_type
            
            agent = self._ecore_classes['Agent'](
                id=data["id"],
                name=data["name"],
                description=data.get("description", ""),
                comment=data.get("comment", ""),
                type=agent_type_enum,
                pos_x=data.get("pos_x", 0.0),
                pos_y=data.get("pos_y", 0.0),
                width=data.get("width", 120.0),
                height=data.get("height", 60.0)
            )
            
            # Ajouter au modèle uniquement si add_to_model est True
            if add_to_model:
                agent.partOf = self.current_model
                self.current_model.agents.append(agent)
            #else:
            #    print(f"Agent {agent.id} créé mais non ajouté au modèle (add_to_model=False).")
            
            return agent
                
        except Exception as e:
            print(f"Erreur lors de la création de l'agent: {e}")
            return None

    def create_resource(self, data, add_to_model=False):
        """
        Crée une nouvelle Resource dans le modèle.
        
        Args:
            data (dict): Données de la ressource
            
        Returns:
            La ressource créée ou None en cas d'erreur
        """
        if not self.current_model:
            return None
        
        try:
            resource = self._ecore_classes['Resource'](
                id=data["id"],
                name=data["name"],
                description=data.get("description", ""),
                comment=data.get("comment", ""),
                unit=data.get("unit", ""),
                quantity=data.get("quantity", 0.0),
                is_renewable=data.get("is_renewable", False),
                pos_x=data.get("pos_x", 0.0),
                pos_y=data.get("pos_y", 0.0),
                width=data.get("width", 120.0),
                height=data.get("height", 60.0)
            )
            
            # Ajouter au modèle uniquement si add_to_model est True
            if add_to_model:
                self.current_model.properties.append(resource)
            return resource
            
        except Exception as e:
            print(f"Erreur lors de la création de la ressource: {e}")
            return None

    def create_parameter(self, data, add_to_model=False):
        """
        Crée un nouveau Parameter dans le modèle.
        
        Args:
            data (dict): Données du paramètre
            
        Returns:
            Le paramètre créé ou None en cas d'erreur
        """
        if not self.current_model:
            return None
        
        try:
            # Vérifier si le paramètre existe déjà
            existing_param = next(
                (p for p in self.current_model.properties 
                 if hasattr(p, 'id') and p.id == data["id"] 
                 and isinstance(p, self._ecore_classes['Parameter'])), 
                None
            )
            
            if existing_param:
                # Mise à jour de l'existant
                self._update_element_attributes(existing_param, data)
                return existing_param

            # Création d'un nouveau paramètre
            parameter = self._ecore_classes['Parameter'](
                id=data["id"],
                name=data["name"],
                description=data.get("description", ""),
                comment=data.get("comment", ""),
                unit=data.get("unit", ""),
                value=data.get("value", ""),
                is_exogenous=data.get("is_exogenous", False),
                parameter_type=data.get("parameter_type", ""),
                pos_x=data.get("pos_x", 0.0),
                pos_y=data.get("pos_y", 0.0),
                width=data.get("width", 120.0),
                height=data.get("height", 60.0)
            )
            
            # Ajouter au modèle uniquement si add_to_model est True
            if add_to_model:
                self.current_model.properties.append(parameter)
            return parameter
            
        except Exception as e:
            print(f"Erreur lors de la création du paramètre: {e}")
            return None

    def create_process(self, data, add_to_model=False):
        """
        Crée un nouveau Process dans le modèle.
        
        Args:
            data (dict): Données du processus
            
        Returns:
            Le processus créé ou None en cas d'erreur
        """
        if not self.current_model:
            return None
        
        try:
            # Déterminer le type de processus
            process_type = data.get("process_type", "TransformationProcess")
            
            if process_type == "TransformationProcess":
                return self._create_transformation_process(data, add_to_model)
            elif process_type == "MovementProcess":
                return self._create_movement_process(data, add_to_model)
            else:
                # Fallback vers Process standard si type non reconnu
                return self._create_generic_process(data, add_to_model)
                
        except Exception as e:
            print(f"Erreur lors de la création du processus: {e}")
            return None

    def _create_generic_process(self, data, add_to_model=False):
        """Crée un Process générique (abstrait, devrait être évité)."""
        process = self._ecore_classes['Process'](
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            comment=data.get("comment", ""),
            equation=data.get("equation", ""),
            pseudo_code=data.get("pseudo_code", ""),
            pos_x=data.get("pos_x", 0.0),
            pos_y=data.get("pos_y", 0.0),
            width=data.get("width", 120.0),
            height=data.get("height", 60.0)
        )
        
        if add_to_model:
            self.current_model.processes.append(process)
        return process

    def _create_transformation_process(self, data, add_to_model=False):
        """Crée un TransformationProcess spécifique."""
        transformation_type_enum = self._ecore_classes['TransformationType'].getEEnumLiteral(
            data.get("transformation_type", "Production")
        )
        
        process = self._ecore_classes['TransformationProcess'](
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            comment=data.get("comment", ""),
            equation=data.get("equation", ""),
            pseudo_code=data.get("pseudo_code", ""),
            transformation_type=transformation_type_enum,
            pos_x=data.get("pos_x", 0.0),
            pos_y=data.get("pos_y", 0.0),
            width=data.get("width", 120.0),
            height=data.get("height", 60.0)
        )
        
        if add_to_model:
            self.current_model.processes.append(process)
        return process

    def _create_movement_process(self, data, add_to_model=False):
        """Crée un MovementProcess spécifique."""
        process = self._ecore_classes['MovementProcess'](
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            comment=data.get("comment", ""),
            equation=data.get("equation", ""),
            pseudo_code=data.get("pseudo_code", ""),
            pos_x=data.get("pos_x", 0.0),
            pos_y=data.get("pos_y", 0.0),
            width=data.get("width", 120.0),
            height=data.get("height", 60.0)
        )
        
        if add_to_model:
            self.current_model.processes.append(process)
        return process

    def _update_element_attributes(self, element, data):
        """
        Met à jour les attributs d'un élément avec les nouvelles données.
        
        Args:
            element: Élément Ecore à mettre à jour
            data (dict): Nouvelles données
        """
        for key, value in data.items():
            if hasattr(element, key):
                setattr(element, key, value)

    # === Gestion des positions et dimensions ===

    def update_element_position(self, element, x, y):
        """
        Met à jour la position d'un élément du modèle.
        
        Args:
            element: Élément Ecore
            x (float): Position X
            y (float): Position Y
        """
        if element and hasattr(element, 'pos_x') and hasattr(element, 'pos_y'):
            element.pos_x = x
            element.pos_y = y
        else:
            print(f"Erreur : Élément invalide ou manque pos_x/pos_y. Type: {type(element)}")

    def update_element_size(self, element_id, width, height):
        """
        Met à jour les dimensions d'un élément par son ID.
        
        Args:
            element_id (str): ID de l'élément
            width (float): Nouvelle largeur
            height (float): Nouvelle hauteur
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        if not self.current_model:
            return False

        element = self._find_element_by_id(element_id)
        
        if element:
            if hasattr(element, 'width'):
                element.width = width
            if hasattr(element, 'height'):
                element.height = height
            return True
            
        return False

    def get_element_by_id(self, element_id):
        """
        Trouve un élément par son ID dans toutes les collections du modèle.
        
        Args:
            element_id (str): ID de l'élément recherché
            
        Returns:
            L'élément trouvé ou None
        """
        return self._find_element_by_id(element_id)

    def _find_element_by_id(self, element_id):
        """
        Trouve un élément par son ID dans toutes les collections du modèle.
        
        Args:
            element_id (str): ID de l'élément recherché
            
        Returns:
            L'élément trouvé ou None
        """
        if not self.current_model:
            return None
            
        all_elements = (
            list(self.current_model.agents) + 
            list(self.current_model.processes) + 
            list(self.current_model.properties)
        )
        
        return next(
            (e for e in all_elements if hasattr(e, 'id') and e.id == element_id), 
            None
        )

    # === Gestion des IDs ===

    def get_existing_ids(self, item_type):
        """
        Génère un nouvel ID unique pour un type d'élément.
        
        Args:
            item_type (str): Type d'élément ('agent', 'resource', etc.)
            
        Returns:
            str: Nouvel ID unique
        """
        base_id = f"{item_type}_"
        counter = 1
        
        # Collecter tous les IDs existants
        existing_ids = []
        if self.resource and self.resource.contents:
            for element in self.resource.contents[0].eAllContents():
                if hasattr(element, 'id'):
                    existing_ids.append(element.id)
        
        # Ajouter les IDs des collections principales
        if self.current_model:
            collections = {
                'agent': self.current_model.agents,
                'resource': [p for p in self.current_model.properties 
                           if isinstance(p, self._ecore_classes['Resource'])],
                'process': self.current_model.processes,
                'parameter': [p for p in self.current_model.properties 
                            if isinstance(p, self._ecore_classes['Parameter'])]
            }
            
            if item_type in collections:
                existing_ids.extend([elem.id for elem in collections[item_type]])

        # Générer un nouvel ID unique
        new_id = f"{base_id}{counter:03d}"
        while new_id in existing_ids:
            counter += 1
            new_id = f"{base_id}{counter:03d}"
            
        return new_id

    # === Gestion des connecteurs ===

    def create_connector_link(self, source, target, conn_type):
        """
        Crée un lien de connecteur entre deux éléments.
        
        Args:
            source: Élément source
            target: Élément cible
            conn_type (str): Type de connexion
            
        Returns:
            tuple: (succès, message)
        """
        #print(f"Création lien: source={source.name}, target={target.name}, type={conn_type}")
        
        success, message = self.validate_connection(source, target, conn_type)
        if not success:
            #print(f"Erreur validation: {message}")
            return False, message
            
        try:
            if conn_type == "holdsResources":
                if target not in source.holdsResources:
                    source.holdsResources.append(target)
                    
            elif conn_type == "isSubjectOf":
                target.subjects = source
                    
            elif conn_type == "isObjectOf":
                #target.object = source
                if target not in source.isObjectOf:
                    source.isObjectOf.append(target)
                    print(f"Création lien: source={source.name}, target={target.name}, type={conn_type}")
                
            elif conn_type == "involvedResources":
                if target not in source.involvedResources:
                    source.involvedResources.append(target)
                    
            elif conn_type == "dependsOnParameters":
                if target not in source.dependsOnParameters:
                    source.dependsOnParameters.append(target)
                    
            elif conn_type == "affectsResources":
                if target not in source.affectsResources:
                    source.affectsResources.append(target)
                    
            elif conn_type == "containsAgents":
                if target not in source.containsAgents:
                    source.containsAgents.append(target)
                    target.partOfParentAgent = source
                    
            elif conn_type == "source":
                source.source = target
                
            elif conn_type == "destination":
                source.destination = target
                
            else:
                return False, f"Type de connexion '{conn_type}' non reconnu"

            #print(f"Lien '{conn_type}' créé entre '{source.name}' et '{target.name}'")
            return True, f"Lien '{conn_type}' créé avec succès"
            
        except Exception as e:
            #print(f"Erreur création lien {conn_type}: {e}")
            return False, f"Erreur lors de la création du lien: {e}"
     

    def delete_connector_link(self, source, target, conn_type):
        """
        Supprime un lien de connecteur entre deux éléments.
        
        Args:
            source: Élément source
            target: Élément cible
            conn_type (str): Type de connexion
            
        Returns:
            tuple: (succès, message)
        """
        try:
            if conn_type == "holdsResources" and hasattr(source, 'holdsResources'):
                if target in source.holdsResources:
                    source.holdsResources.remove(target)
                    
            elif conn_type == "isSubjectOf" and hasattr(target, 'subjects'):
                if source in target.subjects:
                    target.subjects.remove(source)
            
            
            #elif conn_type == "isObjectOf" and hasattr(target, 'objects'):
            #    if target.objects == source:
            #        target.objects = None
                   
            elif conn_type == "isObjectOf" and hasattr(target, 'objects'):
                if source in target.objects:
                    target.objects.remove(source)
                    
            elif conn_type == "involvedResources" and hasattr(source, 'involvedResources'):
                if target in source.involvedResources:
                    source.involvedResources.remove(target)
                    
            elif conn_type == "dependsOnParameters" and hasattr(source, 'dependsOnParameters'):
                if target in source.dependsOnParameters:
                    source.dependsOnParameters.remove(target)
                    
            elif conn_type == "affectsResources" and hasattr(source, 'affectsResources'):
                if target in source.affectsResources:
                    source.affectsResources.remove(target)
                    
            elif conn_type == "containsAgents" and hasattr(source, 'containsAgents'):
                if target in source.containsAgents:
                    source.containsAgents.remove(target)
                    target.partOfParentAgent = None

            # Nettoyage des métadonnées du connecteur
            key = (source.id, target.id, conn_type)
            self.connector_labels.pop(key, None)
            self.control_points.pop(key, None)
            self.connector_types.pop(key, None)
            
            return True, f"Connecteur {conn_type} supprimé"
            
        except Exception as e:
            return False, f"Erreur lors de la suppression : {e}"

    def _load_connector_labels(self, file_path):
        """
        Charge les métadonnées des connecteurs depuis le fichier XMI.
        
        Args:
            file_path (str): Chemin du fichier XMI
            
        Returns:
            tuple: (labels, points_controle, types_connecteurs)
        """
        connector_labels = {}
        control_points = {}
        connector_types = {}
        
        try:
            tree = parse(file_path)
            root = tree.getroot()
            nsmap = root.nsmap
            default_ns = nsmap.get(None, 'http://www.example.org/socioecosystem.en')

            # Parcourir les agents
            for agent_elem in root.findall('.//agents', namespaces=nsmap):
                agent_id = agent_elem.get('id')
                self._load_connectors_from_element(
                    agent_elem, agent_id, connector_labels, control_points, connector_types, nsmap
                )

            # Parcourir les processus
            for process_elem in root.findall('.//processes', namespaces=nsmap):
                process_id = process_elem.get('id')
                self._load_connectors_from_element(
                    process_elem, process_id, connector_labels, control_points, connector_types, nsmap
                )

        except Exception as e:
            print(f"Erreur lors du chargement des labels : {e}")
            
        return connector_labels, control_points, connector_types

    def _load_connectors_from_element(self, element, element_id, labels, points, types, nsmap):
        """
        Charge les connecteurs d'un élément XML spécifique.
        """        
        for ref_elem in element:
            ref_name = ref_elem.tag.split('}')[-1] if '}' in ref_elem.tag else ref_elem.tag
            
            if ref_name in ['holdsResources', 'containsAgents', 'isSubjectOf', 'isObjectOf', 'involvedResources', 
                          'dependsOnParameters', 'affectsResources', 'source', 'destination']:
                target_id = ref_elem.get('href', '')[1:]  # Enlever le '#'
                label = ref_elem.get('label', '')
                control_points_str = ref_elem.get('control_points', '')
                connector_type = ref_elem.get('type', 'straight')
                
                key = (element_id, target_id, ref_name)
                
                if target_id and label:
                    labels[key] = label
                    
                if target_id and control_points_str:
                    points_list = [
                        QPointF(float(x), float(y)) 
                        for x, y in [p.split(',') for p in control_points_str.split(';')]
                    ]
                    points[key] = points_list
                    
                if target_id:
                    types[key] = connector_type

    def update_connector_label(self, source_id, target_id, conn_type, new_label):
        """
        Met à jour le label d'un connecteur.
        """
        key = (source_id, target_id, conn_type)
        if new_label:
            self.connector_labels[key] = new_label
        else:
            self.connector_labels.pop(key, None)
        self.save_model()

    def update_control_points(self, source_id, target_id, conn_type, control_points):
        """
        Met à jour les points de contrôle d'un connecteur.
        """
        key = (source_id, target_id, conn_type)
        if control_points:
            self.control_points[key] = control_points
        else:
            self.control_points.pop(key, None)
        self.save_model()

    # === Suppression d'éléments ===

    def remove_element(self, element):
        """
        Supprime un élément du modèle avec nettoyage des références.
        
        Args:
            element: Élément Ecore à supprimer
        """
        if element.eContainer() is not None:
            container = element.eContainer()
            containment_feature = element.eContainmentFeature()
            container_list = container.eGet(containment_feature)
            
            if container_list is not None and element in container_list:
                # Nettoyage des références avant suppression
                self._clean_element_references(element)
                container_list.remove(element)
            else:
                print(f"Avertissement : Élément non trouvé dans son conteneur")
                
        elif element == self.socioecosystem:
            raise ValueError("Impossible de supprimer l'objet SocioEcosystem racine")

    def _clean_element_references(self, element):
        """
        Nettoie toutes les références pointant vers l'élément à supprimer.
        """
        element_class = element.eClass.name
        
        # Nettoyage dans les agents
        for agent in self.current_model.agents:
            self._remove_from_reference(agent, 'holdsResources', element)
            self._remove_from_reference(agent, 'containsAgents', element)
            self._remove_from_reference(agent, 'isSubjectOf', element, is_subject=True)
            self._remove_from_reference(agent, 'isObjectOf', element, is_object=True)
            
        # Nettoyage dans les processus
        for process in self.current_model.processes:
            self._remove_from_reference(process, 'involvedResources', element)
            self._remove_from_reference(process, 'dependsOnParameters', element)
            self._remove_from_reference(process, 'affectsResources', element)
            self._remove_from_reference(process, 'subjects', element)
            
            if hasattr(process, 'objects') and process.objects == element:
                process.objects = None

    def _remove_from_reference(self, container, ref_name, element, is_subject=False, is_object=False):
        """
        Supprime un élément d'une référence spécifique.
        """
        if hasattr(container, ref_name):
            reference = getattr(container, ref_name)
            if isinstance(reference, list) and element in reference:
                reference.remove(element)
            elif not isinstance(reference, list) and reference == element:
                setattr(container, ref_name, None)

    # === Validation des connexions ===

    def validate_source(self, source_type, conn_type):
        """
        Valide si le type de l'élément source est compatible avec le type de connecteur.
        
        Args:
            source_type (str): Type de l'élément source (ex: "Agent", "Process")
            conn_type (str): Type de connexion (ex: "holdsResources", "isSubjectOf")
            
        Returns:
            bool: True si la source est valide pour ce type de connexion
        """
        # MAPPING des sources valides pour chaque type de connexion
        source_validation_rules = {
            # === RELATIONS AGENT ===
            "holdsResources": ["Agent"],
            "containsAgents": ["Agent"],
            "isSubjectOf": ["Agent"],
            "isObjectOf": ["Agent"],
            
            # === RELATIONS PROCESSUS ===
            "involvedResources": ["Process", "TransformationProcess", "MovementProcess"],
            "dependsOnParameters": ["Process", "TransformationProcess", "MovementProcess"],
            
            # === RELATIONS SPÉCIFIQUES TRANSFORMATIONPROCESS ===
            "affectsResources": ["TransformationProcess"],
            
            # === RELATIONS SPÉCIFIQUES MOVEMENTPROCESS ===
            "source": ["MovementProcess"],
            "destination": ["MovementProcess"]
        }
        
        # Vérifier si le type de connexion est connu
        if conn_type not in source_validation_rules:
            print(f"Type de connexion inconnu: {conn_type}")
            return False
        
        # Vérifier si le type source est autorisé
        allowed_sources = source_validation_rules[conn_type]
        is_valid = source_type in allowed_sources
        
        if not is_valid:
            print(f"Source invalide: {source_type} pour {conn_type}. Sources autorisées: {allowed_sources}")
        
        return is_valid

    def validate_connection(self, source, target, conn_type):
        """
        Valide si une connexion est possible entre deux éléments.
        
        Args:
            source: Élément source
            target: Élément cible
            conn_type (str): Type de connexion
            
        Returns:
            tuple: (succès, message)
        """
        #print(f"🔍 VALIDATION - Source: {source.eClass.name}, Target: {target.eClass.name}, Type: {conn_type}")
    
        try:
            source_type = source.eClass.name
            target_type = target.eClass.name
            
            validation_rules = {
                "holdsResources": (["Agent"], ["Resource"], 
                                "Un agent ne peut détenir que des ressources"),
                "containsAgents": (["Agent"], ["Agent"], 
                                "Un agent ne peut contenir que d'autres agents"),
                "isSubjectOf": (["Agent"], ["Process", "TransformationProcess", "MovementProcess"], 
                            "Seuls les agents peuvent être sujets de processus"),
                "isObjectOf": (["Agent"], ["Process", "TransformationProcess", "MovementProcess"], 
                            "Seuls les agents peuvent être objets de processus"),
                "involvedResources": (["Process", "TransformationProcess", "MovementProcess"], ["Resource"], 
                                "Un processus ne peut impliquer que des ressources"),
                "dependsOnParameters": (["Process", "TransformationProcess", "MovementProcess"], ["Parameter"], 
                                    "Un processus ne peut dépendre que de paramètres"),
                "affectsResources": (["TransformationProcess"], ["Resource"], 
                                "Un processus de transformation n'affecte que des ressources"),
                "source": (["MovementProcess"], ["Agent"],
                        "Un MovementProcess ne peut avoir qu'un Agent comme source"),
                "destination": (["MovementProcess"], ["Agent"],
                            "Un MovementProcess ne peut avoir qu'un Agent comme destination")
            }
            
            if conn_type not in validation_rules:
                return False, f"Type de connexion '{conn_type}' non reconnu"
                
            allowed_sources, allowed_targets, error_msg = validation_rules[conn_type]
            
            if source_type not in allowed_sources:
                return False, f"Source invalide pour {conn_type}: {source_type}"
                
            if target_type not in allowed_targets:
                return False, f"Cible invalide pour {conn_type}: {target_type}"
                
            # Validations spécifiques
            if conn_type == "holdsResources":
                if any(target in agent.holdsResources for agent in self.current_model.agents):
                    return False, "Cette ressource est déjà détenue par un agent"
                    
            elif conn_type == "containsAgents":
                if target.partOfParentAgent is not None:
                    return False, "Cet agent est déjà contenu dans un autre agent"
                    
            elif conn_type == "isSubjectOf":
                if target.subjects is not None:
                    return False, "Cet agent est déjà sujet de ce processus"
                
            elif conn_type == "isObjectOf":
                # target (Processus) a une liste 'objects' (0..*).
                if hasattr(target, 'objects') and source in target.objects:
                    objects_names = [obj.name for obj in target.objects if obj != source]
                    print(f"DEBUG: Processus '{target.name}' objets (excluant la source actuelle): {objects_names}")
                    
                    return False, "Cet agent est déjà l'objet de ce processus"
                else:
                    # 💡 Ajout d'une instruction pour confirmer que nous passons la vérification de doublon
                    print("DEBUG: L'agent n'est pas encore l'objet de ce processus (validation de doublon réussie).")
                    # NE PAS mettre de return True ici, laisser le flux aller au return final
                    
            elif conn_type in ["source", "destination"] and source_type == "MovementProcess":
                if conn_type == "source" and source.source is not None:
                    return False, "MovementProcess a déjà une source"
                elif conn_type == "destination" and source.destination is not None:
                    return False, "MovementProcess a déjà une destination"
                            
            # L'ancienne ligne 'return True, "Connexion valide"' était ici, mal indentée.

            return True, "Connexion valide" # <--- AJOUTEZ LE RETURN FINAL ICI, correctement indenté !
        except Exception as e:
            print(f"❌ ERREUR VALIDATION: {e}")
            return False, f"Erreur de validation: {e}"

    # === Utilitaires ===

    def get_all_elements(self):
        """
        Retourne tous les éléments du modèle courant.
        
        Returns:
            list: Liste de tous les éléments
        """
        if not self.current_model:
            return []
            
        return (
            list(self.current_model.agents) + 
            list(self.current_model.processes) + 
            list(self.current_model.properties)
        )

    def get_ecore_class(self, class_name):
        """
        Retourne une classe Ecore par son nom.
        
        Args:
            class_name (str): Nom de la classe
            
        Returns:
            La classe Ecore ou None
        """
        return self._ecore_classes.get(class_name)