# agent_item.py
from PySide6.QtWidgets import QGraphicsTextItem, QMenu
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtCore import Qt, QRectF, Signal

import sys
from pathlib import Path
# Configuration du path pour les modules locaux
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from baseItem import BaseItem
from dialogs.agentdialog import AgentDialog


class AgentItem(BaseItem):
    # Signaux spécifiques aux Agents
    agent_updated = Signal()
    agent_deleted = Signal()
    
    # Constantes spécifiques aux Agents
    DEFAULT_COLOR = "#FFA500"  # Orange pour les agents
    AGENT_TYPE_COLORS = {
        "Human": "#FFA500",      # Orange
        "Biological": "#90EE90", # Vert clair
        "Physical": "#87CEEB",   # Bleu ciel
        "Social": "#DDA0DD"      # Prune
    }

    def __init__(self, model_element, main_window, parent=None):
        # Appel au constructeur parent
        super().__init__(model_element, main_window, parent)
        self.model_element = model_element  # Garder une référence spécifique
        
        # Mise à jour de la couleur selon le type d'agent
        self._update_color_by_type()
        
        # Mise à jour du texte d'affichage
        self._update_display_text()

    
    def _get_display_text(self):
        """
        Retourne le texte à afficher dans l'item.
        
        Returns:
            str: Texte formaté pour l'affichage
        """
        # Utiliser self.model_element au lieu de self.model_element
        #agent_type = self.model_element.type.name if self.model_element.type else "Human"
        agent_type_obj = getattr(self.model_element, 'type', None)
        if isinstance(agent_type_obj, str):
            agent_type = agent_type_obj
        elif agent_type_obj and hasattr(agent_type_obj, 'name'):
            agent_type = agent_type_obj.name
        else:
            agent_type = "Human"
        return f"{self.model_element.name}\n({agent_type})"


    def _update_color_by_type(self):
        """Met à jour la couleur selon le type d'agent"""
        agent_type_obj = getattr(self.model_element, 'type', None)
        if isinstance(agent_type_obj, str):
            agent_type = agent_type_obj
        elif agent_type_obj and hasattr(agent_type_obj, 'name'):
            agent_type = agent_type_obj.name
        else:
            agent_type = "Human"
        
        color_hex = self.AGENT_TYPE_COLORS.get(agent_type, self.DEFAULT_COLOR)
        self.setBrush(QBrush(QColor(color_hex)))


    def _open_edit_dialog(self):
        """Ouvre le dialogue d'édition spécifique aux Agents"""
        scene = self.scene()
        if not scene or not scene.views():
            return
            
        main_window = scene.views()[0].main_window
        model_manager = main_window.model_manager
        
        # Récupération des données contextuelles depuis le modèle
        current_model = model_manager.current_model
        
        # 1. IDs existants (validation d'unicité)
        existing_agents = current_model.agents if current_model else []
        existing_ids = [agent.id for agent in existing_agents if agent.id != self.model_element.id]

        # 2. PROPRIETES (Parameters) - Conforme au métamodèle
        current_properties = [
            prop for prop in current_model.properties 
            if hasattr(prop, 'eClass') and prop.eClass.name in ['Parameter']
        ] if current_model else []

        # 3. PROCESSUS - Conforme au métamodèle  
        current_processes = current_model.processes if current_model else []

        # 4. RESSOURCES - Conforme au métamodèle
        current_resources = [
            prop for prop in current_model.properties 
            if hasattr(prop, 'eClass') and prop.eClass.name == 'Resource'
        ] if current_model else []
        
        # Relations actuelles de cet agent
        connected_entities = {
            'holdsResources': getattr(self.model_element, 'holdsResources', []),
            'isSubjectOf': getattr(self.model_element, 'isSubjectOf', []),
            'isObjectOf': getattr(self.model_element, 'isObjectOf', []),
            'containsAgents': getattr(self.model_element, 'containsAgents', []),
            'partOfParentAgent': getattr(self.model_element, 'partOfParentAgent', None)
        }

        # Création du dialogue
        dialog = AgentDialog(
            agent=self.model_element,
            parent=main_window,
            existing_ids=existing_ids,
            current_properties=current_properties,      # Parameters 
            current_processes=current_processes,        # Tous les processus
            current_resources=current_resources,        # Toutes les resources
            connected_entities=connected_entities       # Relations existantes
        )
        
        if dialog.exec():
            self._update_from_dialog_data(dialog.get_data())

    def _update_from_dialog_data(self, data):
        """Met à jour l'agent à partir des données du dialogue"""
        # Mise à jour des attributs de base
        self.model_element.id = data["id"]
        self.model_element.name = data["name"]
        self.model_element.type = data["type"]
        self.model_element.description = data.get("description", "")
        self.model_element.comment = data.get("comment", "")
        
        # Mise à jour des relations
        self.model_element.holdsResources = data.get("holdsResources", [])
        self.model_element.isSubjectOf = data.get("isSubjectOf", [])
        self.model_element.isObjectOf = data.get("isObjectOf", [])
        self.model_element.containsAgents = data.get("containsAgents", [])
        self.model_element.partOfParentAgent = data.get("partOfParentAgent", None)
        
        # Mise à jour visuelle
        self._update_display_after_edit()

    def _update_display_after_edit(self):
        """Met à jour l'affichage après édition"""
        # Mise à jour du texte
        self.text_item.setPlainText(self._get_display_text())
        self.update_text_position()
        
        # Mise à jour de la couleur si le type a changé
        self._update_color_by_type()
        
        # Émission du signal de mise à jour
        self.agent_updated.emit()
        
        # Mise à jour des connecteurs
        self._update_connectors()

    def paint(self, painter, option, widget=None):
        """Dessin personnalisé pour les agents"""
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        # Utiliser la couleur actuelle de l'agent
        brush = self.brush()
        pen = self.SELECTED_PEN if self.isSelected() else self.NORMAL_PEN
        
        painter.setBrush(brush)
        painter.setPen(pen)
        
        # Forme arrondie pour les agents
        painter.drawRoundedRect(rect, 10, 10)
        
        # Ajouter un indicateur visuel pour le type si nécessaire
        #self._paint_type_indicator(painter, rect) # afficher au coin haut-froite

    def _paint_type_indicator(self, painter, rect):
        """Ajoute un indicateur visuel pour le type d'agent"""
        indicator_size = 8
        indicator_margin = 4
        
        # Position en haut à droite
        indicator_rect = QRectF(
            rect.right() - indicator_size - indicator_margin,
            rect.top() + indicator_margin,
            indicator_size,
            indicator_size
        )
        
        # Couleur de l'indicateur basée sur le type
        agent_type = getattr(self.model_element, 'type', 'Human')
        color_hex = self.AGENT_TYPE_COLORS.get(agent_type, self.DEFAULT_COLOR)
        indicator_color = QColor(color_hex).darker(150)  # Version plus foncée
        
        painter.setBrush(QBrush(indicator_color))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(indicator_rect)

    def contextMenuEvent(self, event):
        """Menu contextuel spécifique aux agents"""
        menu = QMenu()
        
        # Actions standard
        edit_action = menu.addAction("Éditer l'Agent")
        delete_action = menu.addAction("Supprimer l'Agent")
        menu.addSeparator()
        
        # NOUVELLE ACTION : Ajouter une ressource (notre choix UX)
        add_resource_action = menu.addAction("Ajouter une Ressource")
        menu.addSeparator()
        
        # Actions spécifiques aux agents
        show_relations_action = menu.addAction("Afficher les Relations")
        menu.addSeparator()
        
        # Sous-menu pour le type d'agent
        type_menu = menu.addMenu("Changer le Type")
        human_action = type_menu.addAction("Humain")
        biological_action = type_menu.addAction("Biologique")
        physical_action = type_menu.addAction("Physique")
        social_action = type_menu.addAction("Social")
        
        action = menu.exec(event.screenPos())
        
        if action == edit_action:
            self._open_edit_dialog()
        elif action == delete_action:
            self._delete_item()
        # NOUVEAU CAS : Gestion de l'ajout de ressource
        elif action == add_resource_action:
            self._add_resource_to_agent()
        elif action == show_relations_action:
            self._show_relations()
        elif action == human_action:
            self._change_agent_type("Human")
        elif action == biological_action:
            self._change_agent_type("Biological")
        elif action == physical_action:
            self._change_agent_type("Physical")
        elif action == social_action:
            self._change_agent_type("Social")

    def _add_resource_to_agent(self):
        """
        Déclenche la création d'une ressource contenue par cet agent.
        Appelle la méthode du main_window via la référence parent.
        """
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.create_contained_resource(self)
        else:
            # Fallback si la référence n'est pas disponible
            print("Erreur: Impossible d'accéder à la fenêtre principale pour créer la ressource")

    def _change_agent_type(self, new_type):
        """Change le type de l'agent"""
        self.model_element.type = new_type
        self._update_color_by_type()
        self._update_display_text()
        self.agent_updated.emit()
        self.update()

    def _show_relations(self):
        """Affiche les relations de l'agent (à implémenter)"""
        print(f"Relations de l'agent {self.model_element.name}:")
        print(f"  - Ressources détenues: {len(getattr(self.model_element, 'holdsResources', []))}")
        print(f"  - Processus sujet: {len(getattr(self.model_element, 'isSubjectOf', []))}")
        print(f"  - Processus objet: {len(getattr(self.model_element, 'isObjectOf', []))}")
        print(f"  - Agents contenus: {len(getattr(self.model_element, 'containsAgents', []))}")

    def _update_display_text(self):
        """Met à jour le texte d'affichage"""
        self.text_item.setPlainText(self._get_display_text())
        self.update_text_position()

    def update_from_model(self):
        """Met à jour l'item à partir du modèle"""
        super().update_from_model()
        self._update_color_by_type()
        self._update_display_text()

    def add_outgoing_connector(self, connector):
        """Ajoute un connecteur sortant"""
        self.outgoing_connectors.append(connector)

    def add_incoming_connector(self, connector):
        """Ajoute un connecteur entrant"""
        self.incoming_connectors.append(connector)

    def remove_connector(self, connector):
        """Supprime un connecteur"""
        if connector in self.outgoing_connectors:
            self.outgoing_connectors.remove(connector)
        if connector in self.incoming_connectors:
            self.incoming_connectors.remove(connector)

    def get_related_elements(self):
        """Retourne les éléments liés à cet agent"""
        related = []
        
        # Ressources détenues
        for resource in getattr(self.model_element, 'holdsResources', []):
            related.append(('resource', resource))
            
        # Processus où l'agent est sujet
        for process in getattr(self.model_element, 'isSubjectOf', []):
            related.append(('process_subject', process))
            
        # Processus où l'agent est objet
        for process in getattr(self.model_element, 'isObjectOf', []):
            related.append(('process_object', process))
            
        # Agents contenus
        for agent in getattr(self.model_element, 'containsAgents', []):
            related.append(('contained_agent', agent))
            
        return related