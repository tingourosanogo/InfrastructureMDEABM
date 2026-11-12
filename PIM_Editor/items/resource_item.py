# resource_item.py
from PySide6.QtWidgets import QGraphicsTextItem, QMenu, QGraphicsItem 
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtCore import Qt, QRectF, Signal

import sys
from pathlib import Path
# Configuration du path pour les modules locaux
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from baseItem import BaseItem
from dialogs.resourcedialog import ResourceDialog



class ResourceItem(BaseItem):
    # Signaux spécifiques aux Resources
    resource_updated = Signal()
    resource_deleted = Signal()
    
    # Constantes spécifiques aux Resources
    DEFAULT_COLOR = "#90EE90"  # Vert clair pour les ressources
    RENEWABLE_COLOR = "#90EE90"    # Vert clair pour renouvelable
    NON_RENEWABLE_COLOR = "#F0E68C" # Kaki pour non renouvelable

    def __init__(self, model_element, main_window, parent=None):
        # Appel au constructeur parent
        super().__init__(model_element, main_window, parent)
        self.model_element = model_element  # Garder une référence spécifique
        
        # Mise à jour de la couleur selon le type de ressource
        self._update_color_by_type()
        
        # Mise à jour du texte d'affichage
        self._update_display_text()

    def _get_display_text(self):
        """Retourne le texte à afficher pour la ressource"""
        quantity = getattr(self.model_element, 'quantity', 0)
        unit = getattr(self.model_element, 'unit', '')
        renewable = getattr(self.model_element, 'isRenewable', False)
        
        renewable_text = " (R)" if renewable else " (NR)"
        quantity_text = f"\n{quantity} {unit}" if unit else f"\n{quantity}"
        
        # boite avec plus d'infos
        #return f"{self.model_element.name}{renewable_text}{quantity_text}"

        # boite avec moins d'infos
        return f"{self.model_element.name}{renewable_text}"

    def _update_color_by_type(self):
        """Met à jour la couleur selon le type de ressource"""
        is_renewable = getattr(self.model_element, 'isRenewable', False)
        color_hex = self.RENEWABLE_COLOR if is_renewable else self.NON_RENEWABLE_COLOR
        self.setBrush(QBrush(QColor(color_hex)))

    def _open_edit_dialog(self):
        """Ouvre le dialogue d'édition spécifique aux Resources"""
        scene = self.scene()
        if not scene or not scene.views():
            return
            
        main_window = scene.views()[0].main_window
        model_manager = main_window.model_manager
        current_model = model_manager.current_model

        # 1. RESSOURCES EXISTANTES - Conforme au métamodèle
        existing_resources = [
            prop for prop in current_model.properties 
            if hasattr(prop, 'eClass') and prop.eClass.name == 'Resource'
        ] if current_model else []
        
        existing_ids = [resource.id for resource in existing_resources if resource.id != self.model_element.id]

        # 2. AGENTS - Conforme au métamodèle
        current_agents = current_model.agents if current_model else []

        # 3. ENTITÉS CONNECTÉES (relations actuelles)
        current_relations = {
            'heldBy': getattr(self.model_element, 'heldBy', None)  # Relation inverse de holdsResources
        }

        dialog = ResourceDialog(
            resource=self.model_element,
            parent=main_window,
            existing_ids=existing_ids,
            current_agents=current_agents,        # Tous les agents (pour heldBy)
            connected_entities=current_relations  # Relations existantes
        )
        
        if dialog.exec():
            self._update_from_dialog_data(dialog.get_data())


    def _update_from_dialog_data(self, data):
        """Met à jour la ressource à partir des données du dialogue"""
        # Mise à jour des attributs de base (NamedElement)
        self.model_element.id = data["id"]
        self.model_element.name = data["name"]
        self.model_element.description = data.get("description", "")
        self.model_element.comment = data.get("comment", "")
        
        # Mise à jour des attributs spécifiques à Property
        self.model_element.unit = data.get("unit", "")
        
        # Mise à jour des attributs spécifiques à Resource
        self.model_element.quantity = data.get("quantity", 0.0)
        self.model_element.isRenewable = data.get("isRenewable", False)
        
        # Mise à jour des relations
        self.model_element.heldBy = data.get("heldBy", None)
        
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
        self.resource_updated.emit()
        
        # Mise à jour des connecteurs
        self._update_connectors()

    def paint(self, painter, option, widget=None):
        """Dessin personnalisé pour les ressources"""
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        # Utiliser la couleur actuelle de la ressource
        brush = self.brush()
        pen = self.SELECTED_PEN if self.isSelected() else self.NORMAL_PEN
        
        painter.setBrush(brush)
        painter.setPen(pen)
        
        # Forme rectangulaire avec coins arrondis pour les ressources
        painter.drawRoundedRect(rect, 8, 8)
        
        # Ajouter un indicateur visuel pour le type de ressource
        #self._paint_resource_indicator(painter, rect) # afficher au coin haut-froite

    def _paint_resource_indicator(self, painter, rect):
        """Ajoute un indicateur visuel pour le type de ressource"""
        indicator_size = 6
        indicator_margin = 4
        
        # Position en haut à gauche pour la quantité
        quantity = getattr(self.model_element, 'quantity', 0)
        if quantity > 0:
            # Dessiner un petit cercle avec la quantité
            indicator_rect = QRectF(
                rect.left() + indicator_margin,
                rect.top() + indicator_margin,
                indicator_size,
                indicator_size
            )
            
            # Couleur de l'indicateur basée sur le type renouvelable
            is_renewable = getattr(self.model_element, 'isRenewable', False)
            indicator_color = QColor("#008000" if is_renewable else "#8B4513")  # Vert ou marron
            
            painter.setBrush(QBrush(indicator_color))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawEllipse(indicator_rect)

    def contextMenuEvent(self, event):
        """Menu contextuel spécifique aux ressources"""
        menu = QMenu()
        
        # Actions standard
        edit_action = menu.addAction("Éditer la Ressource")
        delete_action = menu.addAction("Supprimer la Ressource")
        menu.addSeparator()
        
        # Actions spécifiques aux ressources
        show_holders_action = menu.addAction("Afficher les Détenteurs")
        toggle_renewable_action = menu.addAction("Basculer Renouvelable/Non-renouvelable")
        
        action = menu.exec(event.screenPos())
        
        if action == edit_action:
            self._open_edit_dialog()
        elif action == delete_action:
            self._delete_item()
        elif action == show_holders_action:
            self._show_holders()
        elif action == toggle_renewable_action:
            self._toggle_renewable()

    def _toggle_renewable(self):
        """Bascule entre renouvelable et non renouvelable"""
        current_value = getattr(self.model_element, 'isRenewable', False)
        self.model_element.isRenewable = not current_value
        self._update_color_by_type()
        self._update_display_text()
        self.resource_updated.emit()
        self.update()

    def _show_holders(self):
        """Affiche les détenteurs de la ressource"""
        holder = getattr(self.model_element, 'heldBy', None)
        if holder:
            print(f"Ressource {self.model_element.name} détenue par: {holder.name}")
        else:
            print(f"Ressource {self.model_element.name} n'est détenue par aucun agent")

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
        """Retourne les éléments liés à cette ressource"""
        related = []
        
        # Agent détenteur
        holder = getattr(self.model_element, 'heldBy', None)
        if holder:
            related.append(('holder', holder))
            
        # Processus impliquant cette ressource
        # (À implémenter selon la logique métier)
        
        return related

    def itemChange(self, change, value):
        """Surcharge pour émettre le signal spécifique aux ressources"""
        result = super().itemChange(change, value)
        
        if change == QGraphicsItem.ItemPositionChange and self.model_element:
            # Émettre le signal spécifique aux ressources si nécessaire
            pass
            
        return result

    def _delete_item(self):
        """Suppression spécifique de la ressource"""
        if self.main_window and self.main_window.view.scene():
            self.main_window.delete_selected_items([self])
            self.resource_deleted.emit()