"""
Sérialiseur XMI pour le modèle SocioEcosystem.
Convertit le modèle Ecore en format XMI avec support des métadonnées graphiques.
"""
from lxml.etree import Element, SubElement, ElementTree, QName
from pyecore.ecore import EObject
from PySide6.QtCore import QPointF
import uuid
import traceback
import sys
from pathlib import Path

# Configuration du path pour les modules locaux
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class XMLSerializer:
    """
    Gère la sérialisation du modèle SocioEcosystem vers le format XMI.
    
    Responsabilités :
    - Conversion des objets Ecore en XML
    - Préservation des métadonnées graphiques (positions, connecteurs)
    - Gestion des namespaces et types
    """
    
    # Namespaces constants
    XMI_NAMESPACE = 'http://www.omg.org/XMI'
    XSI_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'
    SOCIO_NAMESPACE = 'http://www.example.org/socioecosystem.en'
    
    def __init__(self):
        """Initialise le sérialiseur avec les namespaces par défaut."""
        self.nsmap = {
            None: self.SOCIO_NAMESPACE,
            'xmi': self.XMI_NAMESPACE,
            'xsi': self.XSI_NAMESPACE,
            'ses': self.SOCIO_NAMESPACE  # Préfixe pour le métamodèle
        }

    def serialize_to_xmi(self, model, filename, model_manager, 
                        connector_labels=None, control_points=None, 
                        connector_types=None):
        """
        Sérialise le modèle PyEcore en XMI formaté avec lxml.
        
        Args:
            model: Modèle SocioEcosystem à sérialiser
            filename (str): Chemin du fichier de sortie
            model_manager: Référence au ModelManager pour les résolutions
            connector_labels: Dictionnaire des labels de connecteurs
            control_points: Dictionnaire des points de contrôle
            connector_types: Dictionnaire des types de connecteurs
        """
        try:
            # Créer la racine XMI
            root = self._create_xmi_root()
            
            # Créer l'élément SocioEcosystem principal
            socio_root = self._create_socio_ecosystem_element(root, model)
            
            # Sérialiser tous les éléments du modèle
            
            # 1. SÉRIALISER LES PROPRIÉTÉS EN PREMIER ! (Elles sont souvent cibles de références)
            self._serialize_properties(socio_root, model, connector_labels,
                                    control_points, connector_types)

            # 2. Sérialiser les Processus
            self._serialize_processes(socio_root, model, connector_labels,
                                    control_points, connector_types)
            
            # 3. Sérialiser les Agents
            self._serialize_agents(socio_root, model, connector_labels, 
                                 control_points, connector_types) 

            
            # Écrire le fichier XMI
            self._write_xmi_file(root, filename)
            
        except Exception as e:
            print(f"Erreur lors de la sérialisation XMI : {e}")
            traceback.print_exc()

    def _create_xmi_root(self):
        """
        Crée l'élément racine XMI avec les namespaces appropriés.
        
        Returns:
            Element: Racine XMI configurée
        """
        root = Element(QName(self.XMI_NAMESPACE, 'XMI'), nsmap=self.nsmap)
        root.set(QName(self.XMI_NAMESPACE, 'version'), '2.0')
        return root

    def _create_socio_ecosystem_element(self, parent, model):
        """
        Crée l'élément SocioEcosystem principal.
        
        Args:
            parent: Élément parent XMI
            model: Modèle SocioEcosystem
            
        Returns:
            Element: Élément SocioEcosystem
        """
        socio_elem = SubElement(parent, 'SocioEcosystem')
        socio_elem.set(QName(self.XSI_NAMESPACE, 'type'), 'ses:SocioEcosystem')
        
        # Attributs de base
        self._set_element_attributes(socio_elem, {
            'name': model.name,
            'location': getattr(model, 'location', ''),
            'description': getattr(model, 'description', '')
        })
        
        return socio_elem

    def _serialize_agents(self, parent, model, connector_labels, control_points, connector_types):
        """
        Sérialise tous les agents du modèle.
        """
        for agent in model.agents:
            agent_elem = SubElement(parent, 'agents')
            self._serialize_named_element(agent_elem, agent)
            
             # SECTION : Gérer à la fois strings et enums
            agent_type = getattr(agent, 'type', None)
            if isinstance(agent_type, str):
                type_name = agent_type
            elif agent_type and hasattr(agent_type, 'name'):
                type_name = agent_type.name
            else:
                type_name = 'Human'

            # Attributs spécifiques aux agents
            self._set_element_attributes(agent_elem, {
                'type': type_name
            })
            
            # Références de l'agent
            self._serialize_agent_references(agent_elem, agent, connector_labels,
                                           control_points, connector_types)
            


    def _serialize_agent_references(self, agent_elem, agent, connector_labels, 
                                  control_points, connector_types):
        """
        Sérialise les références d'un agent (relations non-contenantes).
        """
        # Relations avec les processus
        for process in agent.isSubjectOf:
            self._create_reference_element(
                agent_elem, 'isSubjectOf', process, agent.id,
                connector_labels, control_points, connector_types
            )

        for process in agent.isObjectOf:
            self._create_reference_element(
                agent_elem, 'isObjectOf', process, agent.id,
                connector_labels, control_points, connector_types
            )
        
        # Relations de containment d'agents
        for contained_agent in agent.containsAgents:
            self._create_reference_element(
                agent_elem, 'containsAgents', contained_agent, agent.id,
                connector_labels, control_points, connector_types
            )
        
   
        # Relations de containment (opposite)
        if agent.partOfParentAgent:
            self._create_reference_element(
                agent_elem, 'partOfParentAgent', agent.partOfParentAgent, agent.id,
                connector_labels, control_points, connector_types
            )
     
        
        
        # Relations avec les ressources
        for resource in agent.holdsResources:
            self._create_reference_element(
                agent_elem, 'holdsResources', resource, agent.id,
                connector_labels, control_points, connector_types
            )

    def _serialize_processes(self, parent, model, connector_labels, control_points, connector_types):
        """
        Sérialise tous les processus du modèle.
        """
        for process in model.processes:
            process_elem = SubElement(parent, 'processes')
            process_type_name = process.eClass.name
            if process_type_name in ['TransformationProcess', 'MovementProcess']:
                # Ajoute xsi:type="ses:TransformationProcess" ou "ses:MovementProcess"
                process_elem.set(QName(self.XSI_NAMESPACE, 'type'), f'ses:{process_type_name}')
                
            self._serialize_named_element(process_elem, process)
            
            # Attributs communs aux processus
            self._set_element_attributes(process_elem, {
                'equation': getattr(process, 'equation', ''),
                'pseudoCode': getattr(process, 'pseudoCode', '')
            })
            
            # Sérialisation spécifique selon le type de processus
            process_type = process.eClass.name
            if process_type == 'TransformationProcess':
                self._serialize_transformation_process(process_elem, process)
            elif process_type == 'MovementProcess':
                self._serialize_movement_process(process_elem, process)
            
            # Références communes aux processus
            self._serialize_process_references(process_elem, process, connector_labels,
                                             control_points, connector_types)

    def _serialize_transformation_process(self, process_elem, process):
        """
        Sérialise un TransformationProcess spécifique.
        """
        transformation_type = getattr(process, 'transformationType', None)
        if isinstance(transformation_type, str):
            type_name = transformation_type
        elif transformation_type and hasattr(transformation_type, 'name'):
            type_name = transformation_type.name
        else:
            type_name = "Production"

        self._set_element_attributes(process_elem, {
            'transformationType': type_name
        })

    def _serialize_movement_process(self, process_elem, process):
        """
        Sérialise un MovementProcess spécifique.
        """
        # Les relations source et destination sont sérialisées comme références
        pass  # Géré dans _serialize_process_references

    def _serialize_process_references(self, process_elem, process, connector_labels,
                                    control_points, connector_types):
        """
        Sérialise les références d'un processus.
        """
        
        
        # Suject
        if process.subjects:
            self._create_reference_element(
                process_elem, 'subjects', process.subjects, process.id,
                connector_labels, control_points, connector_types
            )
        
        # Objects
        for agent in process.objects:
            self._create_reference_element(
                process_elem, 'objects', agent, process.id,
                connector_labels, control_points, connector_types
            )
            

        # Ressources impliquées
        for resource in process.involvedResources:
            self._create_reference_element(
                process_elem, 'involvedResources', resource, process.id,
                connector_labels, control_points, connector_types
            )
        
        # Paramètres de dépendance
        for parameter in process.dependsOnParameters:
            self._create_reference_element(
                process_elem, 'dependsOnParameters', parameter, process.id,
                connector_labels, control_points, connector_types
            )
        
        # Relations spécifiques aux TransformationProcess
        if process.eClass.name == 'TransformationProcess':
            for resource in process.affectsResources:
                self._create_reference_element(
                    process_elem, 'affectsResources', resource, process.id,
                    connector_labels, control_points, connector_types
                )
        
        # Relations spécifiques aux MovementProcess
        if process.eClass.name == 'MovementProcess':
            if process.source:
                self._create_reference_element(
                    process_elem, 'source', process.source, process.id,
                    connector_labels, control_points, connector_types
                )
            if process.destination:
                self._create_reference_element(
                    process_elem, 'destination', process.destination, process.id,
                    connector_labels, control_points, connector_types
                )

    def _serialize_properties(self, parent, model, connector_labels, control_points, connector_types):
        """
        Sérialise toutes les propriétés (Resources, Parameters) du modèle.
        """
        for prop in model.properties:
            prop_elem = SubElement(parent, 'properties')
            prop_type = prop.eClass.name
            
            # Définir le type XSI approprié
            prop_elem.set(QName(self.XSI_NAMESPACE, 'type'), f'ses:{prop_type}')
            
            # Attributs communs NamedElement
            self._serialize_named_element(prop_elem, prop)
            
            # Attributs communs Property
            self._set_element_attributes(prop_elem, {
                'unit': getattr(prop, 'unit', '')
            })
            
            # Attributs spécifiques selon le type
            if prop_type == 'Resource':
                self._serialize_resource(prop_elem, prop)
            elif prop_type == 'Parameter':
                self._serialize_parameter(prop_elem, prop)

            # Références communes aux processus
            self._serialize_property_references(prop_elem, prop, connector_labels,
                                             control_points, connector_types)

    def _serialize_resource(self, prop_elem, resource):
        """
        Sérialise une Resource spécifique.
        """
        self._set_element_attributes(prop_elem, {
            'quantity': str(getattr(resource, 'quantity', 0.0)),
            'isRenewable': str(getattr(resource, 'isRenewable', False)).lower()
        })


    def _serialize_parameter(self, prop_elem, parameter):
        """
        Sérialise un Parameter spécifique.
        """
        self._set_element_attributes(prop_elem, {
            'value': getattr(parameter, 'value', ''),
            'isExogenous': str(getattr(parameter, 'isExogenous', False)).lower(),
            'parameterType': getattr(parameter, 'parameterType', '')
        })

    def _serialize_property_references(self, prop_elem, prop, connector_labels,
                                    control_points, connector_types):
        """
        Sérialise les références d'unue propriete (resource).
        """
        
        # Relations spécifiques aux MovementProcess
        if prop.eClass.name == 'Resource':
            if prop.heldBy:
                self._create_reference_element(
                    prop_elem, 'heldBy', prop.heldBy, prop.id,
                    connector_labels, control_points, connector_types
                )
    
    
    
    def _serialize_named_element(self, element, named_element):
        """
        Sérialise les attributs communs à tous les NamedElement.
        Garantit l'écriture de xmi:id (pour la résolution PyEcore) et id (pour le modèle).
        """
        
        # 1. VÉRIFICATION DE L'ID (robustesse contre NoneType)
        if named_element.id is None or named_element.id == "":
            # ... (Génération d'ID de secours si vous la conservez)
            unique_id = f"{named_element.eClass.name.lower()}_{uuid.uuid4().hex[:8]}"
            named_element.id = unique_id 
            
        # 2. SÉRIALISATION DE xmi:id (POUR LA RÉSOLUTION DU PROXY)
        xmi_id_qname = QName(self.XMI_NAMESPACE, 'id')
        element.set(xmi_id_qname, named_element.id) # Utilise xmi:id pour l'ID de résolution PyEcore
        
        # 3. CRÉATION DES ATTRIBUTS DE MODÈLE (y compris l'attribut 'id')
        attributes = {
            # Conserve 'id' ici, il sera écrit comme un attribut de modèle simple (id="...")
            'id': named_element.id,
            'name': named_element.name,
            'description': getattr(named_element, 'description', ''),
            'comment': getattr(named_element, 'comment', ''),
            'pos_x': str(getattr(named_element, 'pos_x', 0.0)),
            'pos_y': str(getattr(named_element, 'pos_y', 0.0)),
            'width': str(getattr(named_element, 'width', 120.0)),
            'height': str(getattr(named_element, 'height', 60.0))
        }
        
        self._set_element_attributes(element, attributes)
        

    def _create_reference_element(self, parent, ref_name, target, source_id,
                                connector_labels, control_points, connector_types):
        """
        Crée un élément de référence avec métadonnées graphiques.
        
        Args:
            parent: Élément parent XML
            ref_name (str): Nom de la référence
            target: Élément cible de la référence
            source_id (str): ID de l'élément source
            connector_labels: Dictionnaire des labels
            control_points: Dictionnaire des points de contrôle
            connector_types: Dictionnaire des types de connecteurs
        """
        ref_elem = SubElement(parent, ref_name)
        ref_elem.set('href', f"#{target.id}")
        
        # Clé pour retrouver les métadonnées
        key = (source_id, target.id, ref_name)
        
        # Ajouter le label si présent
        if connector_labels:
            label = connector_labels.get(key, '')
            if label:
                ref_elem.set('label', label)
        
        # Ajouter les points de contrôle si présents
        if control_points:
            points = control_points.get(key, [])
            if points:
                points_str = ";".join(f"{p.x()},{p.y()}" for p in points)
                ref_elem.set('control_points', points_str)
        
        # Ajouter le type de connecteur si présent
        if connector_types:
            connector_type = connector_types.get(key, 'straight')
            ref_elem.set('type', connector_type)

    def _set_element_attributes(self, element, attributes):
        """
        Définit plusieurs attributs sur un élément XML.
        
        Args:
            element: Élément XML cible
            attributes (dict): Dictionnaire attribut → valeur
        """
        for attr, value in attributes.items():
            if value is not None and value != '':
                element.set(attr, str(value))

    def _write_xmi_file(self, root, filename):
        """
        Écrit l'arbre XML dans un fichier.
        
        Args:
            root: Racine de l'arbre XML
            filename (str): Chemin du fichier de sortie
        """
        try:
            tree = ElementTree(root)
            tree.write(filename, pretty_print=True, xml_declaration=True, 
                      encoding='UTF-8')
        except Exception as e:
            print(f"Erreur lors de l'écriture du fichier XMI : {e}")
            raise


# Fonction de compatibilité pour l'ancienne API
def serialize_to_xmi(model, filename, model_manager, connector_labels=None, 
                    control_points=None, connector_types=None):
    """
    Fonction wrapper pour la compatibilité avec l'ancienne API.
    
    Args:
        model: Modèle SocioEcosystem à sérialiser
        filename (str): Chemin du fichier de sortie
        model_manager: Référence au ModelManager
        connector_labels: Dictionnaire des labels de connecteurs
        control_points: Dictionnaire des points de contrôle
        connector_types: Dictionnaire des types de connecteurs
    """
    serializer = XMLSerializer()
    serializer.serialize_to_xmi(model, filename, model_manager, connector_labels,
                              control_points, connector_types)