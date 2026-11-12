# Fichier : commands.py
from PySide6.QtWidgets import QGraphicsItem
from pyecore.ecore import EObject
from PySide6.QtCore import QPointF, QRectF

class Command:
    def undo(self):
        raise NotImplementedError("Méthode undo non implémentée")

    def redo(self):
        raise NotImplementedError("Méthode redo non implémentée")

class AddNodeCommand(Command):
    def __init__(self, main_window, node_item, model_element):
        super().__init__()
        self.main_window = main_window
        self.node_item = node_item
        self.model_element = model_element
        #self.parent_feature = node_item.model_element.eContainmentFeature() if node_item.model_element.eContainer() else None
        #self.parent_container = node_item.model_element.eContainer() if node_item.model_element.eContainer() else None
        
        # Uniquement l'introspection standard
        self.parent_feature = model_element.eContainmentFeature() if model_element.eContainer() else None
        self.parent_container = model_element.eContainer() if model_element.eContainer() else None
        
        # Pour les resources, on laisse la relation holdsResources se faire automatiquement
        # via le métamodèle (puisqu'on a déjà défini heldBy)
        # Détermination sécurisée du parent
        #self._determine_parent_info()

        self.was_added = False
        self.was_in_collections = self._check_if_in_collections()

    # --------------------
    def _determine_parent_info(self):
        """Détermine de manière sécurisée le conteneur parent et la feature."""
        try:
            # Cas 1: Resource avec heldBy (contenue par un agent)
            if hasattr(self.model_element, 'heldBy') and self.model_element.heldBy:
                self.parent_container = self.model_element.heldBy
                #self.parent_feature = self.parent_container.eClass.getEStructuralFeature('holdsResources')
                self.parent_feature = self.parent_container.eClass.eStructuralFeatures['holdsResources']
                return
                
            # Cas 2: Élément avec eContainer() (contenu standard)
            if self.model_element.eContainer():
                self.parent_container = self.model_element.eContainer()
                self.parent_feature = self.model_element.eContainmentFeature()
                return
                
            # Cas 3: Élément à la racine - déterminer la feature par type
            self.parent_container = self.main_window.model_manager.current_model
            self.parent_feature = self._get_root_feature()
            
        except Exception as e:
            print(f"⚠️ Erreur détermination parent: {e}")
            self.parent_container = None
            self.parent_feature = None

    def _get_root_feature(self):
        """Retourne la feature appropriée pour les éléments racines."""
        feature_mapping = {
            'Agent': 'agents',
            'Process': 'processes',
            'TransformationProcess': 'processes', 
            'MovementProcess': 'processes',
            'Resource': 'properties',
            'Parameter': 'properties'
        }
        
        element_type = self.model_element.eClass.name
        feature_name = feature_mapping.get(element_type, 'properties')
        
        return self.parent_container.eClass.getEStructuralFeature(feature_name)
    # --------------------

    def _check_if_in_collections(self):
        """Vérifie si l'élément est déjà dans les collections du modèle."""
        if self.parent_container and self.parent_feature:
            container_list = self.parent_container.eGet(self.parent_feature)
            return self.model_element in container_list
        return False

    def undo(self):
        if self.was_added:
            # Supprimer de la scène
            self.main_window.scene.removeItem(self.node_item)
            
            # Supprimer des collections seulement si on l'avait ajouté
            if self.parent_container and self.parent_feature and not self.was_in_collections:
                container_list = self.parent_container.eGet(self.parent_feature)
                if self.model_element in container_list:
                    container_list.remove(self.model_element)
                    print(f"Agent {self.model_element.id} supprimé du modèle dans undo.")
            
            if self.model_element.id in self.main_window.model_to_item:
                del self.main_window.model_to_item[self.model_element.id]
            self.was_added = False
            
            self.main_window.update_navigation_tree()
            self.main_window.model_manager.save_model()

    def redo(self):
        if not self.was_added:
            # Ajouter à la scène
            self.main_window.scene.addItem(self.node_item)
            
            # Ajouter aux collections seulement si pas déjà présent
            if self.parent_container and self.parent_feature:
                container_list = self.parent_container.eGet(self.parent_feature)
                if self.model_element not in container_list:
                    container_list.append(self.model_element)
                    #print(f"Agent {self.model_element.id} ajouté au modèle dans redo.")
            
            self.main_window.model_to_item[self.model_element.id] = self.node_item
            self.was_added = True
            
            self.main_window.update_navigation_tree()
            self.main_window.model_manager.save_model()
            
# ------------------------------------------------------------------------------------------
class DeleteNodeCommand(Command): 
    def __init__(self, main_window, node_item, model_element):
        self.main_window = main_window
        self.node_item = node_item
        self.model_element = model_element
        self.parent_container = model_element.eContainer()
        self.parent_feature = model_element.eContainmentFeature() 
        self.cascaded_deletions = [] # Liste pour les Resources/Parameters à supprimer

        self.debug_cascade_detection(model_element)

        # 1. Sauvegarder les connecteurs du NŒUD PRIMAIRE
        # Votre logique existante est déplacée vers une méthode d'aide pour la réutilisation.
        self.outgoing_connectors = self._get_connector_data(node_item.outgoing_connectors)
        self.incoming_connectors = self._get_connector_data(node_item.incoming_connectors)
        
        # 2. Identifier et sauvegarder les éléments à supprimer en cascade
        self.cascaded_deletions = self._get_cascaded_deletions(model_element)

    def _get_connector_data(self, connector_list):
        """Extrait et stocke les données nécessaires pour restaurer un connecteur."""
        data = []
        for connector in list(connector_list):
            # Utilisez try/except si source/target peuvent être None (nœud en cours de création)
            source = connector.source.model_element
            target = connector.target.model_element
            conn_type = connector.conn_type
            style_data = connector.get_style_data()
            data.append((connector, source, target, conn_type, style_data))
        return data

    def _get_cascaded_deletions(self, model_element: EObject):
        """
        Détermine les éléments à supprimer en cascade par analyse des relations.
        """
        cascaded_list = []
        class_name = model_element.eClass.name
        element_id = model_element.id
        
        # 1. CAS AGENT : Trouver les Resources via la relation inverse heldBy
        if class_name == 'Agent':
            for resource in self.main_window.model_manager.current_model.properties:
                if (resource.eClass.name == 'Resource' and 
                    hasattr(resource, 'heldBy') and 
                    resource.heldBy and 
                    resource.heldBy.id == element_id):
                    self._add_cascaded_element(resource, cascaded_list, "Resource de l'Agent")
        
        # 2. CAS PROCESSUS : Trouver les Parameters exclusifs
        elif class_name in ['Process', 'TransformationProcess', 'MovementProcess']:
            for parameter in self.main_window.model_manager.current_model.properties:
                if parameter.eClass.name == 'Parameter':
                    # Vérifier si ce Parameter n'est utilisé que par ce Process
                    if self._is_parameter_exclusive_to_process_id(parameter, element_id):
                        self._add_cascaded_element(parameter, cascaded_list, "Parameter exclusif du Process")
        
        return cascaded_list

    def _is_parameter_exclusive_to_process_id(self, parameter, process_id):
        """
        Vérifie si un Parameter n'est utilisé que par un Process spécifique.
        """
        # Trouver le Process par ID
        target_process = None
        for process in self.main_window.model_manager.current_model.processes:
            if process.id == process_id:
                target_process = process
                break
        
        if not target_process:
            return False
        
        # Vérifier l'utilisation exclusive
        for process in self.main_window.model_manager.current_model.processes:
            if (process != target_process and 
                hasattr(process, 'dependsOnParameters') and 
                parameter in process.dependsOnParameters):
                return False  # Utilisé par un autre Process
        
        # Vérifier que le Parameter est bien utilisé par le Process cible
        return (hasattr(target_process, 'dependsOnParameters') and 
                parameter in target_process.dependsOnParameters)

    def _add_cascaded_element(self, model_element, cascaded_list, reason):
        """
        Ajoute un élément à la liste des cascades avec vérifications.
        """
        cascaded_item = self.main_window.model_to_item.get(model_element)
        
        if cascaded_item:
            cascaded_list.append({
                'model': model_element,
                'item': cascaded_item,
                'parent': model_element.eContainer(),
                'feature': model_element.eContainmentFeature(),
                'outgoing_conns': self._get_connector_data(cascaded_item.outgoing_connectors),
                'incoming_conns': self._get_connector_data(cascaded_item.incoming_connectors),
                'reason': reason  # Pour le debug
            })
            print(f"🔗 Cascade: {reason} - {model_element.name}")
            
    # ---------------------------------------------
    def debug_cascade_detection(self, model_element):
        """
        Méthode de debug pour comprendre pourquoi les cascades ne sont pas détectées.
        """
        print(f"\n=== DEBUG CASCADE POUR {model_element.eClass.name} {model_element.id} ===")
        
        # Afficher toutes les relations de l'élément
        print("Relations de l'élément:")
        for feature in model_element.eClass.eAllReferences():
            try:
                value = model_element.eGet(feature)
                print(f"  {feature.name}: {value}")
            except:
                print(f"  {feature.name}: ERREUR")
        
        # Afficher les Resources dans le modèle
        print("\nResources dans le modèle:")
        for prop in self.main_window.model_manager.current_model.properties:
            if prop.eClass.name == 'Resource':
                held_by = getattr(prop, 'heldBy', None)
                held_by_id = held_by.id if held_by else "None"
                print(f"  {prop.id} -> heldBy: {held_by_id}")
        
        # Afficher les Parameters et leurs dépendances
        print("\nParameters dans le modèle:")
        for prop in self.main_window.model_manager.current_model.properties:
            if prop.eClass.name == 'Parameter':
                # Trouver les processus qui dépendent de ce Parameter
                dependent_processes = []
                for process in self.main_window.model_manager.current_model.processes:
                    if (hasattr(process, 'dependsOnParameters') and 
                        prop in process.dependsOnParameters):
                        dependent_processes.append(process.id)
                print(f"  {prop.id} -> dépend de: {dependent_processes}")
        
        # Tester la détection
        cascades = self._get_cascaded_deletions(model_element)
        print(f"\nCascades détectées: {len(cascades)}")
        for cascade in cascades:
            print(f"  - {cascade['model'].id} ({cascade['reason']})")
    # ---------------------------------------------
        
    
    def redo(self):
        # 0. Aides pour la suppression de connecteurs (à placer dans la classe ou dans une classe d'aide)
        self._remove_cascaded_and_primary_elements(delete_cascaded=True, delete_primary=True)

    def _remove_connector_from_scene_and_model(self, connector, source_model, target_model, conn_type):
        """Méthode utilitaire pour supprimer un connecteur (graphique et Ecore)."""
        # Supprimer le lien Ecore
        self.main_window.model_manager.delete_connector_link(source_model, target_model, conn_type)
        
        # Supprimer l'élément graphique et le retirer des listes de ses parents
        if connector in connector.source.outgoing_connectors:
            connector.source.outgoing_connectors.remove(connector)
        if connector in connector.target.incoming_connectors:
            connector.target.incoming_connectors.remove(connector)
        self.main_window.view.scene().removeItem(connector)

    def _remove_cascaded_and_primary_elements(self, delete_cascaded, delete_primary):
        """
        Supprime les éléments avec gestion robuste des relations Ecore.
        """
        
        # 1. Suppression des éléments en cascade
        if delete_cascaded:
            for data in self.cascaded_deletions:
                # Supprimer les connecteurs
                all_conns = data['outgoing_conns'] + data['incoming_conns']
                for connector, source, target, conn_type, _ in all_conns:
                    self._remove_connector_from_scene_and_model(connector, source, target, conn_type)
                
                # Nettoyage complet des relations
                self._cleanup_element_relations(data['model'])
                
                # Suppression graphique et mapping
                self.main_window.scene.removeItem(data['item'])
                self.main_window.model_to_item.pop(data['model'].id, None)
                
                # Suppression Ecore
                self._remove_from_ecore_container(data['model'], data['parent'], data['feature'])

        # 2. Suppression de l'élément primaire
        if delete_primary:
            # Supprimer les connecteurs
            all_conns = self.outgoing_connectors + self.incoming_connectors
            for connector, source, target, conn_type, _ in all_conns:
                self._remove_connector_from_scene_and_model(connector, source, target, conn_type)
            
            # Nettoyage complet des relations
            self._cleanup_element_relations(self.model_element)
            
            # Suppression graphique et mapping
            self.main_window.scene.removeItem(self.node_item)
            self.main_window.model_to_item.pop(self.model_element.id, None)
            
            # Suppression Ecore
            self._remove_from_ecore_container(self.model_element, self.parent_container, self.parent_feature)

        # Finalisation
        self.main_window.update_navigation_tree()
        self.main_window.model_manager.save_model()

    def _cleanup_element_relations(self, element):
        """
        Nettoie toutes les relations référençant cet élément.
        Évite les références pendantes dans le modèle.
        """
        element_type = element.eClass.name
        
        if element_type == 'Agent':
            self._cleanup_agent_relations(element)
        elif element_type == 'Resource':
            self._cleanup_resource_relations(element)
        elif element_type in ['Process', 'TransformationProcess', 'MovementProcess']:
            self._cleanup_process_relations(element)
        elif element_type == 'Parameter':
            self._cleanup_parameter_relations(element)

    def _cleanup_agent_relations(self, agent):
        """Nettoie les relations référençant un Agent."""
        # Nettoyer les références dans les Processus
        for process in self.main_window.model_manager.current_model.processes:
            if agent in process.subjects:
                process.subjects.remove(agent)
            if agent in getattr(process, 'objects', []):
                process.objects.remove(agent)
            if hasattr(process, 'source') and process.source == agent:
                process.source = None
            if hasattr(process, 'destination') and process.destination == agent:
                process.destination = None

    def _cleanup_resource_relations(self, resource):
        """Nettoie les relations référençant une Resource."""
        # Nettoyer les références dans les Processus
        for process in self.main_window.model_manager.current_model.processes:
            if resource in process.involvedResources:
                process.involvedResources.remove(resource)
            if hasattr(process, 'affectsResources') and resource in process.affectsResources:
                process.affectsResources.remove(resource)

    def _cleanup_process_relations(self, process):
        """Nettoie les relations référençant un Process."""
        # Nettoyer les références dans les Agents
        for agent in self.main_window.model_manager.current_model.agents:
            if process in agent.isSubjectOf:
                agent.isSubjectOf.remove(process)
            if process in agent.isObjectOf:
                agent.isObjectOf.remove(process)

    def _cleanup_parameter_relations(self, parameter):
        """Nettoie les relations référençant un Parameter."""
        # Nettoyer les références dans les Processus
        for process in self.main_window.model_manager.current_model.processes:
            if parameter in process.dependsOnParameters:
                process.dependsOnParameters.remove(parameter)

    def _remove_from_ecore_container(self, element, parent, feature):
        """
        Supprime un élément de son conteneur Ecore de manière robuste.
        """
        if parent and feature:
            try:
                container_attr = parent.eGet(feature)
                if feature.many:
                    if element in container_attr:
                        container_attr.remove(element)
                else:
                    if container_attr == element:
                        parent.eSet(feature, None)
            except Exception as e:
                print(f"⚠️ Erreur suppression Ecore {element.eClass.name}: {e}")

    # ======================
    def undo(self):
        # 0. Aides pour la restauration de connecteurs (à placer dans la classe ou dans une classe d'aide)
        self._restore_cascaded_and_primary_elements(restore_cascaded=True, restore_primary=True)

    # Déplacez cette logique dans DeleteNodeCommand
    def _restore_connector_to_scene_and_model(self, connector, source_model, target_model, conn_type, style_data):
        """Méthode utilitaire pour restaurer un connecteur (graphique et Ecore)."""
        # 1. Rétablir le lien Ecore
        # NOTE: create_connector_link DOIT gérer l'ajout du lien (ex: source.holdsResources.append(target))
        self.main_window.model_manager.create_connector_link(source_model, target_model, conn_type)

        # 2. Rétablir l'élément graphique
        self.main_window.view.scene().addItem(connector)
        
        # 3. Rétablir les listes de connecteurs des nœuds source/cible
        if connector not in connector.source.outgoing_connectors:
            connector.source.outgoing_connectors.append(connector) 
        if connector not in connector.target.incoming_connectors:
            connector.target.incoming_connectors.append(connector)
            
        # 4. Remettre les control points
        connector.restore_style_data(style_data) 


    def _restore_cascaded_and_primary_elements(self, restore_cascaded, restore_primary):
        """
        Restaure les éléments supprimés (en cascade puis primaire) sur la scène
        graphique et dans le modèle Ecore.
        """
        
        # 1. Restauration des éléments en cascade (Resources/Parameters)
        if restore_cascaded:
            for data in self.cascaded_deletions:
                
                # A. Rétablir l'élément Ecore en cascade
                parent = data['parent']
                feature = data['feature']
                model = data['model']

                if parent and feature:
                    container_attr = parent.eGet(feature)
                    if feature.many and model not in container_attr:
                        # Le conteneur est une collection (ex: SocioEcosystem.properties)
                        container_attr.append(model)
                    elif not feature.many:
                        # Relation 1..1
                        parent.eSet(feature, model)
                
                # B. Rétablir l'élément graphique en cascade
                self.main_window.view.scene().addItem(data['item'])
                self.main_window.model_to_item[data['model']] = data['item']
                
                # C. Rétablir les connecteurs du nœud en cascade
                all_cascaded_conns = data['outgoing_conns'] + data['incoming_conns']
                for connector, source, target, conn_type, style_data in all_cascaded_conns:
                    self._restore_connector_to_scene_and_model(connector, source, target, conn_type, style_data)
                        
        # 2. Restauration du NŒUD PRIMAIRE (Agent ou Process)
        if restore_primary:
            
            # A. Rétablir l'élément Ecore PRIMAIRE
            parent_container = self.parent_container
            parent_feature = self.parent_feature
            model_element = self.model_element
            
            if parent_container and parent_feature:
                container_attr = parent_container.eGet(parent_feature)
                if parent_feature.many and model_element not in container_attr:
                    # Le conteneur est une collection (ex: SocioEcosystem.agents)
                    container_attr.append(model_element)
                elif not parent_feature.many:
                    parent_container.eSet(parent_feature, model_element)
                    
            # B. Rétablir l'élément graphique PRIMAIRE
            self.main_window.view.scene().addItem(self.node_item)
            self.main_window.model_to_item[self.model_element] = self.node_item

            # C. Restaurer les connecteurs du NŒUD PRIMAIRE
            all_primary_conns = self.outgoing_connectors + self.incoming_connectors
            for connector, source, target, conn_type, style_data in all_primary_conns:
                self._restore_connector_to_scene_and_model(connector, source, target, conn_type, style_data)

        # 3. Finalisation
        self.main_window.update_navigation_tree()
        self.main_window.model_manager.save_model()
        

    

# ------------------------------------------------------------------------------------------
class AddConnectorCommand(Command):
    def __init__(self, main_window, connector_item, source, target, conn_type):
        self.main_window = main_window
        self.connector_item = connector_item
        self.source = source  # Modèle source (ex. Agent)
        self.target = target  # Modèle cible (ex. Resource ou Process)
        self.conn_type = conn_type  # Type de connexion (ex. 'owns', 'hasProcesses')

    def undo(self):
        # Supprimer le connecteur graphique et la référence dans le modèle
        if self.connector_item.scene():
            self.connector_item.scene().removeItem(self.connector_item)
        self.main_window.model_manager.delete_connector_link(self.source, self.target, self.conn_type)
        self.main_window.update_navigation_tree()
        self.main_window.model_manager.save_model()

    def redo(self):
        # Réajouter le connecteur graphique et la référence dans le modèle
        self.main_window.model_manager.create_connector_link(self.source, self.target, self.conn_type)
        if self.connector_item.scene() is None:
            self.main_window.scene.addItem(self.connector_item)
        self.main_window.update_navigation_tree()
        self.main_window.model_manager.save_model()

# Dans commands.py (Classe d'origine, modifiée pour être complète)

class DeleteConnectorCommand(Command):
    def __init__(self, main_window, connector_item, source, target, conn_type):
        self.main_window = main_window
        self.connector_item = connector_item
        self.source = source
        self.target = target
        self.conn_type = conn_type
        # Sauvegarder les données graphiques pour le 'undo'

    def undo(self):
        # 1. Rétablir le lien Ecore
        success, _ = self.main_window.model_manager.create_connector_link(self.source, self.target, self.conn_type)
        if success:
            # 2. Rétablir l'élément graphique
            self.main_window.view.scene().addItem(self.connector_item)
            self.connector_item.source.outgoing_connectors.append(self.connector_item)
            self.connector_item.target.incoming_connectors.append(self.connector_item)
            self.connector_item.restore_style_data(self.style_data)
        
            self.main_window.update_navigation_tree()
            self.main_window.model_manager.save_model()


    def redo(self):
        # 1. Supprimer le lien Ecore
        self.main_window.model_manager.delete_connector_link(self.source, self.target, self.conn_type)
        
        # 2. Supprimer l'élément graphique
        self.main_window.view.scene().removeItem(self.connector_item)
        if self.connector_item in self.connector_item.source.outgoing_connectors:
            self.connector_item.source.outgoing_connectors.remove(self.connector_item)
        if self.connector_item in self.connector_item.target.incoming_connectors:
            self.connector_item.target.incoming_connectors.remove(self.connector_item)
            
        self.main_window.update_navigation_tree()
        self.main_window.model_manager.save_model()


class ModifyConnectorCommand(Command):
    def __init__(self, main_window, connector_item, old_state, new_state):
        self.main_window = main_window
        self.connector_item = connector_item
        self.old_state = old_state  # Dictionnaire contenant l'état avant modification
        self.new_state = new_state  # Dictionnaire contenant l'état après modification

    def undo(self):
        # Restaurer l'état précédent
        self.connector_item.label_item.setPlainText(self.old_state['label'])
        self.connector_item.setToolTip(self.old_state['label'])
        self.connector_item.update_label_position()
        self.connector_item.connector_type = self.old_state['type']
        self.connector_item.style["type"] = self.old_state['type']
        if self.old_state['type'] in ["curved"]:
            self.connector_item.control_points = self.old_state['control_points']
            self.connector_item.control_points_updated_signal.emit(
                self.connector_item.source.model_element.id,
                self.connector_item.target.model_element.id,
                self.connector_item.conn_type,
                self.old_state['control_points']
            )
        self.connector_item.connector_type_updated_signal.emit(
            self.connector_item.source.model_element.id,
            self.connector_item.target.model_element.id,
            self.connector_item.conn_type,
            self.old_state['type']
        )
        self.connector_item.update_path()
        self.main_window.update_navigation_tree()
        self.main_window.model_manager.save_model()

    def redo(self):
        # Appliquer l'état modifié
        self.connector_item.label_item.setPlainText(self.new_state['label'])
        self.connector_item.setToolTip(self.new_state['label'])
        self.connector_item.update_label_position()
        self.connector_item.connector_type = self.new_state['type']
        self.connector_item.style["type"] = self.new_state['type']
        if self.new_state['type'] in ["curved"]:
            self.connector_item.control_points = self.new_state['control_points']
            self.connector_item.control_points_updated_signal.emit(
                self.connector_item.source.model_element.id,
                self.connector_item.target.model_element.id,
                self.connector_item.conn_type,
                self.new_state['control_points']
            )
        self.connector_item.connector_type_updated_signal.emit(
            self.connector_item.source.model_element.id,
            self.connector_item.target.model_element.id,
            self.connector_item.conn_type,
            self.new_state['type']
        )
        self.connector_item.update_path()
        self.main_window.update_navigation_tree()
        self.main_window.model_manager.save_model()


class ModifyFieldCommand(Command):
    def __init__(self, main_window, element, field_name, old_value, new_value):
        self.main_window = main_window
        self.element = element  # Élément EObject modifié (ex. Agent, Process)
        self.field_name = field_name  # Nom de l'attribut modifié (ex. 'name', 'documentation')
        self.old_value = old_value
        self.new_value = new_value

    def undo(self):
        # Restaurer l'ancienne valeur
        setattr(self.element, self.field_name, self.old_value)
        self.main_window.update_navigation_tree()
        self.main_window.model_manager.save_model()

    def redo(self):
        # Appliquer la nouvelle valeur
        setattr(self.element, self.field_name, self.new_value)
        self.main_window.update_navigation_tree()
        self.main_window.model_manager.save_model()


class MoveNodeCommand(Command):
    def __init__(self, main_window, node_item, old_pos, new_pos):
        self.main_window = main_window
        self.node_item = node_item
        self.model_element = node_item.model_element
        self.old_pos = old_pos  # QPointF pour l'ancienne position
        self.new_pos = new_pos  # QPointF pour la nouvelle position

    def undo(self):
        if self.model_element:
            self.model_element.pos_x = self.old_pos.x()
            self.model_element.pos_y = self.old_pos.y()
            self.node_item.setPos(self.old_pos)
            self.main_window.update_navigation_tree()
            self.main_window.model_manager.save_model()

    def redo(self):
        if self.model_element:
            self.model_element.pos_x = self.new_pos.x()
            self.model_element.pos_y = self.new_pos.y()
            self.node_item.setPos(self.new_pos)
            self.main_window.update_navigation_tree()
            self.main_window.model_manager.save_model()


class ResizeNodeCommand(Command):
    def __init__(self, main_window, node_item, old_size, new_size):
        self.main_window = main_window
        self.node_item = node_item
        self.model_element = node_item.model_element
        self.old_size = old_size  # Tuple (width, height) ancien
        self.new_size = new_size  # Tuple (width, height) nouveau

    def undo(self):
        if self.model_element:
            self.model_element.width = self.old_size[0]
            self.model_element.height = self.old_size[1]
            self.node_item.setRect(QRectF(0, 0, self.old_size[0], self.old_size[1]))
            self.node_item.update_text_position()  # Mettre à jour le texte si nécessaire
            self.main_window.update_navigation_tree()
            self.main_window.model_manager.save_model()

    def redo(self):
        if self.model_element:
            self.model_element.width = self.new_size[0]
            self.model_element.height = self.new_size[1]
            self.node_item.setRect(QRectF(0, 0, self.new_size[0], self.new_size[1]))
            self.node_item.update_text_position()  # Mettre à jour le texte si nécessaire
            self.main_window.update_navigation_tree()
            self.main_window.model_manager.save_model()


class DeleteItemsCommand(Command):
    def __init__(self, main_window, items):
        self.main_window = main_window
        self.items = items  # Liste des items supprimés
        self.models = [item.model_element for item in items if hasattr(item, 'model_element')]

    def undo(self):
        for item in self.items:
            self.main_window.scene.addItem(item)
        self.main_window.update_navigation_tree()

    def redo(self):
        for item in self.items:
            self.main_window.scene.removeItem(item)
        self.main_window.update_navigation_tree()

class PasteItemsCommand(Command):
    def __init__(self, main_window, pasted_items):
        self.main_window = main_window
        self.pasted_items = pasted_items

    def undo(self):
        for item in self.pasted_items:
            self.main_window.scene.removeItem(item)
        self.main_window.update_navigation_tree()

    def redo(self):
        for item in self.pasted_items:
            self.main_window.scene.addItem(item)
        self.main_window.update_navigation_tree()