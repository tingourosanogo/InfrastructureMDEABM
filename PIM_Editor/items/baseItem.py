# baseItem.py
from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsTextItem, QStyleOptionGraphicsItem,
    QWidget, QGraphicsItem, QMenu
)
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from PySide6.QtCore import Qt, QRectF, Signal, QObject, QPointF

from commands import MoveNodeCommand, ResizeNodeCommand


class BaseItem(QObject, QGraphicsRectItem):
    # Signaux communs à tous les items
    item_updated = Signal()
    item_deleted = Signal()
    item_moved = Signal(str, float, float)
    item_resized = Signal(str, float, float)
    
    # Constantes communes
    MIN_WIDTH = 80.0
    MIN_HEIGHT = 40.0
    DEFAULT_WIDTH = 150.0
    DEFAULT_HEIGHT = 45.0
    
    # Couleurs par défaut (peuvent être surchargées)
    DEFAULT_COLOR = "#FF6347"
    SELECTED_PEN = QPen(Qt.red, 2, Qt.DashLine)
    NORMAL_PEN = QPen(Qt.black, 2)

    def __init__(self, model_element, main_window, parent=None):
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self, parent)
        
        self.model_element = model_element
        self.main_window = main_window
        
        # Connecteurs
        self.outgoing_connectors = []
        self.incoming_connectors = []
        
        # Dimensions
        width = self._get_valid_width()
        height = self._get_valid_height()
        
        self.setRect(QRectF(0, 0, width, height))
        self.setBrush(QBrush(QColor(self.DEFAULT_COLOR)))
        self.setPen(self.NORMAL_PEN)
        self.setCursor(Qt.OpenHandCursor)
        
        # Flags communs
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable
            | QGraphicsRectItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )

        # Élément texte
        self.text_item = QGraphicsTextItem(self._get_display_text(), self)
        self.text_item.setDefaultTextColor(Qt.white)
        self.update_text_position()

        # Événements
        self.setAcceptHoverEvents(True)
        
        # État de redimensionnement
        self.resizing = None
        self.start_resize_pos = QPointF()
        self.start_rect = QRectF()
        self.old_pos = self.pos()
        self.old_size = (width, height)

    def _get_valid_width(self):
        """Retourne la largeur valide (avec valeurs par défaut si nécessaire)"""
        if hasattr(self.model_element, 'width') and self.model_element.width > self.MIN_WIDTH:
            return self.model_element.width
        return self.DEFAULT_WIDTH

    def _get_valid_height(self):
        """Retourne la hauteur valide (avec valeurs par défaut si nécessaire)"""
        if hasattr(self.model_element, 'height') and self.model_element.height > self.MIN_HEIGHT:
            return self.model_element.height
        return self.DEFAULT_HEIGHT

    def _get_display_text(self):
        """Retourne le texte à afficher (peut être surchargé)"""
        return getattr(self.model_element, 'name', 'Unknown')

    def update_text_position(self):
        """Centre le texte dans l'hexagone - version optimisée"""
        rect = self.rect()
        
        # Calculer la zone disponible dans l'hexagone
        hexagon_width = rect.width() * 0.85
        hexagon_height = rect.height() * 0.85
        
        # Ajuster la largeur texte à la zone hexagonale
        self.text_item.setTextWidth(hexagon_width - 40)
        
        text_rect = self.text_item.boundingRect()
        
        # Centrer dans la zone hexagonale
        x = (rect.width() - text_rect.width()) / 2
        y = (rect.height() - text_rect.height()) / 2 - (rect.height() * 0.075)  # 🔥 Ajustement fin
        
        self.text_item.setPos(x, y)

    def itemChange(self, change, value):
        """Gestion des changements de position et mise à jour des connecteurs"""
        if change == QGraphicsItem.ItemPositionChange and self.model_element:
            new_pos = value
            self._update_model_position(new_pos)
            
        if change == QGraphicsItem.ItemPositionHasChanged:
            self._update_connectors()
            
        return super().itemChange(change, value)

    def _update_model_position(self, new_pos):
        """Met à jour la position dans le modèle"""
        try:
            self.model_element.pos_x = new_pos.x()
            self.model_element.pos_y = new_pos.y()
            self.item_moved.emit(self.model_element.id, new_pos.x(), new_pos.y())
        except AttributeError as e:
            print(f"Erreur: Impossible de persister la position: {e}")

    def update_from_model(self):
        """Met à jour l'affichage à partir du modèle"""
        self.setRect(QRectF(0, 0, self._get_valid_width(), self._get_valid_height()))
        self.text_item.setPlainText(self._get_display_text())
        self.update_text_position()

    def _update_connectors(self):
        """Met à jour tous les connecteurs liés à cet item"""
        for connector in self.outgoing_connectors + self.incoming_connectors:
            connector.update_path()

    def mousePressEvent(self, event):
        """Gestion du clic souris - Pattern Template Method"""
        if event.button() == Qt.LeftButton:
            scene = self.scene()
            if not scene or not scene.views():
                super().mousePressEvent(event)
                return
            
            main_window = scene.views()[0].main_window
            
            # 1. Mode redimensionnement
            if self.resizing:
                self.start_resize_pos = event.screenPos()
                self.start_rect = self.rect()
                event.accept()
                return
            
            # 2. Mode connexion
            elif main_window.connection_mode:
                self._handle_connection_mode(main_window)
                event.ignore()
                return
            
            # 3. Mode normal
            else:
                self.setCursor(Qt.ClosedHandCursor)
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def _handle_connection_mode(self, main_window):
        """Gère le mode connexion (peut être étendu)"""
        mode = main_window.connection_mode
        if not main_window.connection_source:
            main_window.connection_source = self
            main_window.statusBar().showMessage(f"Source: {self.model_element.name}. Cible pour '{mode}'?")
            self.setCursor(Qt.ArrowCursor)
        else:
            main_window.connection_target = self

    def mouseMoveEvent(self, event):
        """Gestion du mouvement souris"""
        if self.resizing:
            self._handle_resizing(event)
            event.accept()
            return
        
        super().mouseMoveEvent(event)
        
        # Émission en temps réel du mouvement
        if QGraphicsItem.ItemIsMovable in self.flags():
            self.item_moved.emit(self.model_element.id, self.x(), self.y())

    def _handle_resizing(self, event):
        """Gère le redimensionnement"""
        delta = event.screenPos() - self.start_resize_pos
        new_rect = QRectF(self.start_rect)
        
        new_width = self.start_rect.width()
        new_height = self.start_rect.height()
        
        if 'right' in self.resizing:
            new_width = max(self.MIN_WIDTH, self.start_rect.width() + delta.x())
        if 'bottom' in self.resizing:
            new_height = max(self.MIN_HEIGHT, self.start_rect.height() + delta.y())
            
        new_rect.setWidth(new_width)
        new_rect.setHeight(new_height)
        
        self.prepareGeometryChange()
        self.setRect(new_rect)
        self.update_text_position()
        self.item_resized.emit(self.model_element.id, new_rect.width(), new_rect.height())

    def mouseReleaseEvent(self, event):
        """Gestion du relâchement souris - Commandes undo/redo"""
        if self.resizing:
            new_size = (self.rect().width(), self.rect().height())
            if new_size != self.old_size and self.model_element:
                self.main_window.execute_command(
                    ResizeNodeCommand(self.main_window, self, self.old_size, new_size)
                )
                self.old_size = new_size
            self.resizing = None
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            new_pos = self.pos()
            if new_pos != self.old_pos and self.model_element:
                self.main_window.execute_command(
                    MoveNodeCommand(self.main_window, self, self.old_pos, new_pos)
                )
                self.old_pos = new_pos
            self.setCursor(Qt.OpenHandCursor)
        
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Ouvre le dialogue d'édition - À implémenter dans les classes filles"""
        self._open_edit_dialog()
        super().mouseDoubleClickEvent(event)

    def _open_edit_dialog(self):
        """Méthode abstraite à implémenter dans les classes filles"""
        raise NotImplementedError("_open_edit_dialog must be implemented in subclass")

    def keyPressEvent(self, event):
        """Gestion des touches clavier"""
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace) and self.isSelected():
            self.scene().views()[0].delete_selected_items()
            event.accept()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Menu contextuel"""
        menu = QMenu()
        delete_action = menu.addAction("Supprimer")
        action = menu.exec(event.screenPos())
        if action == delete_action:
            self._delete_item()

    def _delete_item(self):
        """Suppression de l'item"""
        if self.main_window and self.main_window.view.scene():
            self.main_window.delete_selected_items([self])
            self.item_deleted.emit()

    def hoverMoveEvent(self, event):
        """Gestion du survol pour le redimensionnement"""
        pos = event.pos()
        rect = self.rect()
        border_size = 5

        # Détection des zones de redimensionnement
        if (rect.bottomRight() - pos).manhattanLength() < border_size * 2:
            self.setCursor(Qt.SizeFDiagCursor)
            self.resizing = 'bottom_right'
        elif abs(rect.right() - pos.x()) < border_size:
            self.setCursor(Qt.SizeHorCursor)
            self.resizing = 'right'
        elif abs(rect.bottom() - pos.y()) < border_size:
            self.setCursor(Qt.SizeVerCursor)
            self.resizing = 'bottom'
        else:
            if not self._is_connection_mode_active():
                self.setCursor(Qt.OpenHandCursor)
                self.resizing = None
            else:
                self.setCursor(Qt.ArrowCursor)
                self.resizing = None
                
        super().hoverMoveEvent(event)

    def _is_connection_mode_active(self):
        """Vérifie si le mode connexion est actif"""
        scene = self.scene()
        if scene and scene.views():
            return scene.views()[0].main_window.connection_mode
        return False

    def hoverLeaveEvent(self, event):
        """Rétablit le curseur quand la souris quitte l'item"""
        if not self._is_connection_mode_active():
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)

    def setHighlight(self, state: bool):
        """
        Active ou désactive une surbrillance visuelle autour de l'élément.
        Utilisé pour marquer l'élément source en mode connexion.
        """
        self._highlight_active = state
        self.update()
        
    '''
    def paint(self, painter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Dessin de l'item - Peut être surchargé pour des styles spécifiques"""
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        # Utiliser la couleur spécifique de la classe ou la couleur par défaut
        brush = QBrush(QColor(self.DEFAULT_COLOR))
        pen = self.SELECTED_PEN if self.isSelected() else self.NORMAL_PEN
        
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 5, 5)
    '''
    

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """
        Modifie la méthode paint pour dessiner la surbrillance.
        """
        # Couleur du trait par défaut (bordure)
        if self.isSelected():
            pen_color = Qt.yellow
            pen_width = 3
        elif hasattr(self, '_highlight_active') and self._highlight_active:
            # 💡 AJOUT : Surbrillance rouge pour la connexion
            pen_color = Qt.red
            pen_width = 3
        else:
            pen_color = Qt.black
            pen_width = 2
            
        pen = QPen(pen_color, pen_width)
        painter.setPen(pen)
        
        # Le fond est géré par la sous-classe (AgentItem, ProcessItem, etc.)
        # Assurez-vous d'appeler super().paint() si BaseNodeItem implémente le dessin du rectangle
        # Pour une QGraphicsRectItem, vous pouvez simplement dessiner le contour avec le bon QPen
        painter.drawRect(self.rect())

    