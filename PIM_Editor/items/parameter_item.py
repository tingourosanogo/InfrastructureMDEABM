# parameter_item.py
from PySide6.QtWidgets import QGraphicsTextItem, QMenu
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtCore import Qt, QRectF, Signal

import sys
from pathlib import Path
# Configuration du path pour les modules locaux
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from baseItem import BaseItem
from dialogs.propertydialog import ParameterDialog  # Le dialogue s'appelle ParameterDialog dans propertydialog.py


class ParameterItem(BaseItem):
    # Signaux spécifiques aux Parameters
    parameter_updated = Signal()
    parameter_deleted = Signal()
    
    # Constantes spécifiques aux Parameters
    DEFAULT_COLOR = "#A9A9A9"  # Gris clair pour les paramètres
    EXOGENOUS_COLOR = "#D3D3D3"  # Gris plus clair pour exogène
    ENDOGENOUS_COLOR = "#808080"  # Gris plus foncé pour endogène

    def __init__(self, model_element, main_window, parent=None):
        # Appel au constructeur parent
        super().__init__(model_element, main_window, parent)
        self.model_element = model_element  # Garder une référence spécifique
        
        # Mise à jour de la couleur selon le type de paramètre
        self._update_color_by_type()
        
        # Mise à jour du texte d'affichage
        self._update_display_text()

    def _get_display_text(self):
        """Retourne le texte à afficher pour le paramètre"""
        value = getattr(self.model_element, 'value', '')
        unit = getattr(self.model_element, 'unit', '')
        is_exogenous = getattr(self.model_element, 'isExogenous', False)
        param_type = getattr(self.model_element, 'parameterType', 'float')
        
        exogenous_text = " (Exo)" if is_exogenous else " (Endo)"
        type_text = f"\nType: {param_type}" if param_type and param_type != "float" else ""
        value_text = f"\nValeur: {value}" if value else ""
        unit_text = f" {unit}" if unit and value else ""
        
        
        # boite avec moins d'infos
        display_text = f"Param: {self.model_element.name}{exogenous_text}"
        '''
        # boite avec plus d'infos
        if type_text:
            display_text += type_text
        if value_text:
            display_text += value_text + unit_text
        '''

        #display_text = f"Param: {self.model_element.name}" # boite avec juste le nom du parameter

        return display_text

    def _update_color_by_type(self):
        """Met à jour la couleur selon le type de paramètre"""
        is_exogenous = getattr(self.model_element, 'isExogenous', False)
        color_hex = self.EXOGENOUS_COLOR if is_exogenous else self.ENDOGENOUS_COLOR
        self.setBrush(QBrush(QColor(color_hex)))

    def _open_edit_dialog(self):
        """Ouvre le dialogue d'édition spécifique aux Parameters"""
        scene = self.scene()
        if not scene or not scene.views():
            return
            
        main_window = scene.views()[0].main_window
        model_manager = main_window.model_manager
        
        # Récupération des données contextuelles depuis le modèle
        current_model = model_manager.current_model
        
        # Parameters existants (pour la validation des IDs)
        existing_parameters = current_model.properties if current_model else []
        existing_ids = [param.id for param in existing_parameters if param.id != self.model_element.id]
        
        # Création du dialogue - Utilisation de ParameterDialog
        dialog = ParameterDialog(
            parameter=self.model_element,
            parent=main_window,
            existing_ids=existing_ids
        )
        
        if dialog.exec():
            self._update_from_dialog_data(dialog.get_data())

    def _update_from_dialog_data(self, data):
        """Met à jour le paramètre à partir des données du dialogue"""
        # Mise à jour des attributs de base (NamedElement)
        self.model_element.id = data["id"]
        self.model_element.name = data["name"]
        self.model_element.description = data.get("description", "")
        self.model_element.comment = data.get("comment", "")
        
        # Mise à jour des attributs spécifiques à Property
        self.model_element.unit = data.get("unit", "")
        
        # Mise à jour des attributs spécifiques à Parameter
        self.model_element.value = data.get("value", "")
        self.model_element.isExogenous = data.get("isExogenous", False)
        self.model_element.parameterType = data.get("parameterType", "float")
        
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
        self.parameter_updated.emit()

    def paint(self, painter, option, widget=None):
        """Dessin personnalisé pour les paramètres"""
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        # Utiliser la couleur actuelle du paramètre
        brush = self.brush()
        pen = self.SELECTED_PEN if self.isSelected() else self.NORMAL_PEN
        
        painter.setBrush(brush)
        painter.setPen(pen)
        
        # Forme rectangulaire avec coins arrondis pour les paramètres
        painter.drawRoundedRect(rect, 6, 6)
        
        # Ajouter un indicateur visuel pour le type de paramètre
        #self._paint_parameter_indicator(painter, rect) # afficher au coin haut-froite

    def _paint_parameter_indicator(self, painter, rect):
        """Ajoute un indicateur visuel pour le type de paramètre"""
        indicator_size = 8
        indicator_margin = 4
        
        # Position en haut à droite pour le type exogène/endogène
        is_exogenous = getattr(self.model_element, 'isExogenous', False)
        
        # Dessiner un petit symbole
        indicator_rect = QRectF(
            rect.right() - indicator_size - indicator_margin,
            rect.top() + indicator_margin,
            indicator_size,
            indicator_size
        )
        
        # Couleur et symbole selon le type
        if is_exogenous:
            # Symbole "E" pour exogène
            painter.setPen(QPen(Qt.black, 1))
            painter.drawText(indicator_rect, Qt.AlignCenter, "E")
        else:
            # Symbole "I" pour endogène
            painter.setPen(QPen(Qt.black, 1))
            painter.drawText(indicator_rect, Qt.AlignCenter, "I")

    def contextMenuEvent(self, event):
        """Menu contextuel spécifique aux paramètres"""
        menu = QMenu()
        
        # Actions standard
        edit_action = menu.addAction("Éditer le Paramètre")
        delete_action = menu.addAction("Supprimer le Paramètre")
        menu.addSeparator()
        
        # Actions spécifiques aux paramètres
        toggle_exogenous_action = menu.addAction("Basculer Exogène/Endogène")
        
        action = menu.exec(event.screenPos())
        
        if action == edit_action:
            self._open_edit_dialog()
        elif action == delete_action:
            self._delete_item()
        elif action == toggle_exogenous_action:
            self._toggle_exogenous()

    def _toggle_exogenous(self):
        """Bascule entre exogène et endogène"""
        current_value = getattr(self.model_element, 'isExogenous', False)
        self.model_element.isExogenous = not current_value
        self._update_color_by_type()
        self._update_display_text()
        self.parameter_updated.emit()
        self.update()

    def _update_display_text(self):
        """Met à jour le texte d'affichage"""
        self.text_item.setPlainText(self._get_display_text())
        self.update_text_position()

    def update_from_model(self):
        """Met à jour l'item à partir du modèle"""
        super().update_from_model()
        self._update_color_by_type()
        self._update_display_text()

    def _delete_item(self):
        """Suppression spécifique du paramètre"""
        if self.main_window and self.main_window.view.scene():
            self.main_window.delete_selected_items([self])
            self.parameter_deleted.emit()