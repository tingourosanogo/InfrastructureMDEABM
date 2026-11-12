from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsItem, QMenu, QStyle
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QPainterPathStroker
from PySide6.QtCore import QLineF, QPointF, Qt, QObject, Signal, QRectF, QSizeF, QEvent

import sys
from pathlib import Path
# Configuration du path pour les modules locaux
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from commands import ModifyConnectorCommand

class ConnectorHandle(QGraphicsEllipseItem):
    def __init__(self, connector, is_source):
        super().__init__(QRectF(-5, -5, 10, 10))
        self.connector = connector
        self.is_source = is_source
        self.setPen(QPen(QColor(self.connector.style.get("color", Qt.black)), 2, self.connector.style.get("style", Qt.SolidLine)))
        self.setBrush(QBrush(QColor("blue")))
        self.setZValue(-1)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.update_position()

    def update_position(self):
        if self.is_source:
            pos = self.connector.source.sceneBoundingRect().center()
        else:
            pos = self.connector.target.sceneBoundingRect().center()
        self.setPos(pos - QPointF(5, 5))
        line = QLineF(self.connector.source.sceneBoundingRect().center(), 
                      self.connector.target.sceneBoundingRect().center())
        self.setToolTip(f"Handle {'source' if self.is_source else 'target'}: Distance = {line.length():.0f} px")

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("lightblue")))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor("blue")))
        super().hoverLeaveEvent(event)

class ControlPointHandle(QGraphicsEllipseItem):
    def __init__(self, connector, index):
        super().__init__(QRectF(-5, -5, 10, 10))
        self.connector = connector
        self.index = index
        self.setPen(QPen(QColor("black"), 1))
        self.setBrush(QBrush(QColor("blue")))
        self.setZValue(1)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.update_position()

    def update_position(self):
        if 0 <= self.index < len(self.connector.control_points):
            self.setPos(self.connector.control_points[self.index] - QPointF(5, 5))
        source_center = self.connector.source.sceneBoundingRect().center()
        distance = QLineF(source_center, self.connector.control_points[self.index]).length()
        self.setToolTip(f"Point de contrôle {self.index + 1}: Distance au source = {distance:.0f} px")

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            new_pos = self.pos() + QPointF(5, 5)
            self.connector.control_points[self.index] = new_pos
            self.connector.update_path()
            self.connector.update_relative_t()
            self.connector.control_points_updated_signal.emit(
                self.connector.source.model_element.id,
                self.connector.target.model_element.id,
                self.connector.conn_type,
                self.connector.control_points
            )
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction("Supprimer point de contrôle")
        action = menu.exec_(event.screenPos())
        if action == delete_action:
            self.connector.remove_control_point(self.index)

class ConnectorItem(QObject, QGraphicsPathItem):
    connector_deleted_signal = Signal(object, object, str)
    connector_label_updated_signal = Signal(str, str, str, str)
    control_points_updated_signal = Signal(str, str, str, list)
    connector_type_updated_signal = Signal(str, str, str, str)

    def __init__(self, source_item, target_item, conn_type, style, control_points, main_window, parent=None):
        QObject.__init__(self)
        QGraphicsPathItem.__init__(self, parent)
        self.source = source_item
        self.target = target_item
        self.conn_type = conn_type
        self.style = style if style is not None else {"color": "black", "width": 2, "style": Qt.SolidLine, "type": "straight"}
        self.control_points = control_points if control_points is not None else []
        self.connector_type = self.style.get("type", "straight")
        #self.old_label = self.style.get("label", conn_type)
        self.old_label = self.style.get("label", '') # Utilisez le label ou une chaîne vide
        self.relative_t = []
        self.relative_offsets = []
        self.setPen(QPen(QColor(self.style.get("color", Qt.black)), self.style.get("width", 2), self.style.get("style", Qt.SolidLine)))
        self.setZValue(-1)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemUsesExtendedStyleOption, True)
        self.setAcceptHoverEvents(True)
        self.setToolTip(self.style.get("label", conn_type))

        #self.label_item = QGraphicsTextItem(self.style.get("label", conn_type), self)
        self.label_item = QGraphicsTextItem(self.style.get("label", ''), self)
        self.label_item.setDefaultTextColor(QColor(self.style.get("color", Qt.black)))
        self.label_item.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.label_item.setAcceptHoverEvents(True)
        self.label_item.setToolTip(f"Label pour {self.conn_type}")
        self.label_item.focusOutEvent = self.on_label_focus_out

        self.source_handle = ConnectorHandle(self, is_source=True)
        self.target_handle = ConnectorHandle(self, is_source=False)
        self.control_point_handles = []
        self.update_path()
        self.update_relative_t()

        # Ajout de la référence à MainWindow
        self.main_window = main_window

    # -------------------
    def install_event_filters(self):
        if (self.scene() is not None and
            self.source.scene() is not None and
            self.target.scene() is not None and
            self.source.scene() == self.scene() and
            self.target.scene() == self.scene()):
            self.source.installSceneEventFilter(self)
            self.target.installSceneEventFilter(self)
            #print("sceneEventFilter installé pour source et target")
        else:
            print("Échec installation sceneEventFilter :",
                  "source.scene() =", self.source.scene(),
                  "target.scene() =", self.target.scene(),
                  "self.scene() =", self.scene())

    # -------------------
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.update_control_point_handles()
            else:
                for handle in self.control_point_handles:
                    if handle.scene():
                        handle.scene().removeItem(handle)
                self.control_point_handles.clear()
        return super().itemChange(change, value)

    # -------------------
    def sceneEventFilter(self, item, event):
        #print("Événement reçu dans sceneEventFilter :", event.type())
        if event.type() == QEvent.GraphicsSceneMouseRelease:
            if item == self.source or item == self.target:
                #print("Déplacement détecté pour", "source" if item == self.source else "target")
                self.recalculate_control_points()
                self.control_points_updated_signal.emit(
                    self.source.model_element.id,
                    self.target.model_element.id,
                    self.conn_type,
                    self.control_points
                )
        return super().sceneEventFilter(item, event)

    # -------------------
    def update_path(self):
        if not self.source or not self.target:
            return
        path = QPainterPath()
        source_center = self.source.sceneBoundingRect().center()
        target_center = self.target.sceneBoundingRect().center()
        path.moveTo(source_center)

        if not self.control_points and self.connector_type in ["curved", "rounded", "orthogonal"]:
            self.control_points = self.generate_control_points()
            self.control_points_updated_signal.emit(
                self.source.model_element.id,
                self.target.model_element.id,
                self.conn_type,
                self.control_points
            )

        if self.connector_type == "straight":
            path.lineTo(target_center)
        elif self.connector_type == "curved":
            if self.control_points:
                points = [source_center] + self.control_points + [target_center]
                tension = 0.5
                for i in range(len(points) - 1):
                    p0 = points[max(0, i - 1)]
                    p1 = points[i]
                    p2 = points[i + 1]
                    p3 = points[min(len(points) - 1, i + 2)]
                    c1 = QPointF(p1.x() + (p2.x() - p0.x()) * tension / 6, p1.y() + (p2.y() - p0.y()) * tension / 6)
                    c2 = QPointF(p2.x() - (p3.x() - p1.x()) * tension / 6, p2.y() - (p3.y() - p1.y()) * tension / 6)
                    path.cubicTo(c1, c2, p2)
            else:
                path.lineTo(target_center)
        elif self.connector_type == "rounded":
            if self.control_points:
                current = source_center
                radius = 15
                for i, point in enumerate(self.control_points):
                    prev_point = current
                    next_point = self.control_points[i + 1] if i + 1 < len(self.control_points) else target_center
                    dx_prev = point.x() - prev_point.x()
                    dy_prev = point.y() - prev_point.y()
                    dx_next = next_point.x() - point.x()
                    dy_next = next_point.y() - point.y()
                    if abs(dx_prev) > abs(dy_prev):
                        path.lineTo(QPointF(point.x() - radius * (-1 if dx_prev < 0 else 1), point.y()))
                    else:
                        path.lineTo(QPointF(point.x(), point.y() - radius * (-1 if dy_prev < 0 else 1)))
                    arc_rect = QRectF(point.x() - radius, point.y() - radius, 2 * radius, 2 * radius)
                    if abs(dx_next) > abs(dy_next):
                        start_angle = 90 if dx_next > 0 else -90
                        sweep_angle = 90 * (-1 if dy_prev < 0 else 1) * (1 if dx_prev > 0 else -1)
                    else:
                        start_angle = 180 if dy_next > 0 else 0
                        sweep_angle = 90 * (1 if dx_prev < 0 else -1) * (-1 if dy_next > 0 else 1)
                    path.arcTo(arc_rect, start_angle, sweep_angle)
                    current = point
                path.lineTo(target_center)
            else:
                path.lineTo(target_center)
        elif self.connector_type == "orthogonal":
            if self.control_points:
                current = source_center
                for point in self.control_points:
                    path.lineTo(QPointF(point.x(), current.y()))
                    path.lineTo(point)
                    current = point
                path.lineTo(QPointF(target_center.x(), current.y()))
                path.lineTo(target_center)
            else:
                mid_x = (source_center.x() + target_center.x()) / 2
                path.lineTo(QPointF(mid_x, source_center.y()))
                path.lineTo(QPointF(mid_x, target_center.y()))
                path.lineTo(target_center)

        self.setPath(path)
        self.source_handle.update_position()
        self.target_handle.update_position()
        self.update_label_position()
        for handle in self.control_point_handles:
            handle.update_position()
        
    # -------------------
    def update_relative_t(self):
        self.relative_t = []
        self.relative_offsets = []
        if self.connector_type != "curved":
            return
        source_center = self.source.sceneBoundingRect().center()
        target_center = self.target.sceneBoundingRect().center()
        path = QPainterPath()
        path.moveTo(source_center)
        if self.control_points:
            points = [source_center] + self.control_points + [target_center]
            tension = 0.5
            for i in range(len(points) - 1):
                p0 = points[max(0, i - 1)]
                p1 = points[i]
                p2 = points[i + 1]
                p3 = points[min(len(points) - 1, i + 2)]
                c1 = QPointF(p1.x() + (p2.x() - p0.x()) * tension / 6, p1.y() + (p2.y() - p0.y()) * tension / 6)
                c2 = QPointF(p2.x() - (p3.x() - p1.x()) * tension / 6, p2.y() - (p3.y() - p1.y()) * tension / 6)
                path.cubicTo(c1, c2, p2)
        else:
            path.lineTo(target_center)
        
        path_length = path.length()
        if path_length == 0:
            return
        
        line = QLineF(source_center, target_center)
        for point in self.control_points:
            closest_t = 0.0
            min_distance = float('inf')
            for t in [i / 100 for i in range(101)]:
                test_point = path.pointAtPercent(t)
                distance = QLineF(point, test_point).length()
                if distance < min_distance:
                    min_distance = distance
                    closest_t = t
            self.relative_t.append(closest_t)
            self.relative_offsets.append(0.0)
        
        #print("relative_t=", self.relative_t, "relative_offsets=", self.relative_offsets)

    # -------------------
    def recalculate_control_points(self):
        if self.connector_type != "curved":
            return
        source_center = self.source.sceneBoundingRect().center()
        target_center = self.target.sceneBoundingRect().center()
        path = QPainterPath()
        path.moveTo(source_center)
        points = [source_center] + self.control_points + [target_center]
        tension = 0.5
        for i in range(len(points) - 1):
            p0 = points[max(0, i - 1)]
            p1 = points[i]
            p2 = points[i + 1]
            p3 = points[min(len(points) - 1, i + 2)]
            c1 = QPointF(p1.x() + (p2.x() - p0.x()) * tension / 6, p1.y() + (p2.y() - p0.y()) * tension / 6)
            c2 = QPointF(p2.x() - (p3.x() - p1.x()) * tension / 6, p2.y() - (p3.y() - p1.y()) * tension / 6)
            path.cubicTo(c1, c2, p2)
        
        new_points = []
        for t in self.relative_t:
            new_point = path.pointAtPercent(t)
            new_points.append(new_point)
        
        self.control_points = new_points
        self.update_control_point_handles()
        self.update_path()
        self.update_relative_t()
        self.control_points_updated_signal.emit(
            self.source.model_element.id,
            self.target.model_element.id,
            self.conn_type,
            self.control_points
        )
        print("recalculated control_points=", self.control_points)

    # -------------------
    def generate_control_points(self):
        if not self.source or not self.target:
            return []
        source_center = self.source.sceneBoundingRect().center()
        target_center = self.target.sceneBoundingRect().center()
        line = QLineF(source_center, target_center)
        distance = line.length()
        # MODIFICATION : Génération dynamique à la Draw.io (1-5 points, espacement ~120 px)
        num_points = max(1, min(5, int(distance // 120)))
        points = []
        
        connector_type = self.connector_type
        
        if connector_type == "straight":
            for i in range(num_points):
                t = (i + 1) / (num_points + 1)
                x = source_center.x() + t * (target_center.x() - source_center.x())
                y = source_center.y() + t * (target_center.y() - source_center.y())
                points.append(QPointF(x, y))
        
        elif connector_type == "curved":
            # Points pour Catmull-Rom, espacés avec léger décalage pour fluidité
            for i in range(num_points):
                t = (i + 1) / (num_points + 1)
                x = source_center.x() + t * (target_center.x() - source_center.x())
                y = source_center.y() + t * (target_center.y() - source_center.y())
                offset = distance * 0.05 * ((-1) ** i)
                if abs(target_center.y() - source_center.y()) > abs(target_center.x() - source_center.x()):
                    y += offset
                else:
                    x += offset
                points.append(QPointF(x, y))
        
        elif connector_type == "rounded":
            for i in range(num_points):
                t = (i + 1) / (num_points + 1)
                x = source_center.x() + t * (target_center.x() - source_center.x())
                y = source_center.y() + t * (target_center.y() - source_center.y())
                points.append(QPointF(x, y))
        
        elif connector_type == "orthogonal":
            for i in range(num_points):
                t = (i + 1) / (num_points + 1)
                if i % 2 == 0:
                    x = source_center.x() + t * (target_center.x() - source_center.x())
                    y = source_center.y()
                else:
                    x = source_center.x() + (t - 0.5) * (target_center.x() - source_center.x())
                    y = source_center.y() + t * (target_center.y() - source_center.y())
                points.append(QPointF(x, y))
        
        return points
    
    # -------------------
    def shape(self):
        path = self.path()
        if path.isEmpty():
            return QPainterPath()
        stroker = QPainterPathStroker()
        stroker.setWidth(2.0)
        stroker.setCapStyle(Qt.RoundCap)
        stroker.setJoinStyle(Qt.RoundJoin)
        return stroker.createStroke(path)
    
    # -------------------
    def boundingRect(self):
        shape_path = self.shape()
        if shape_path.isEmpty():
            return QRectF()
        return shape_path.boundingRect()
        

    # -------------------
    def paint(self, painter, option, widget=None):
        option.state &= ~QStyle.State_Selected
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.save()
            highlight_pen = QPen(QColor(0, 120, 215), 2.0, Qt.DashLine)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(self.shape())
            # AJOUT : Preview visuel lors du drag
            if self.preview_path and self.connector_type == "curved":
                preview_pen = QPen(QColor(100, 149, 237, 150), 1.5, Qt.DotLine)
                painter.setPen(preview_pen)
                painter.drawPath(self.preview_path)
            painter.restore()
        self.preview_path = None  # Réinitialiser après peinture

    
    #************************************#

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction("Supprimer")
        rename_action = menu.addAction("Renommer le label")
        change_type_action = menu.addMenu("Changer type de connecteur")
        change_type_action.addAction("Droit").triggered.connect(lambda: self.set_connector_type("straight"))
        change_type_action.addAction("Courbé").triggered.connect(lambda: self.set_connector_type("curved"))
        change_type_action.addAction("Arrondi").triggered.connect(lambda: self.set_connector_type("rounded"))
        change_type_action.addAction("Orthogonal").triggered.connect(lambda: self.set_connector_type("orthogonal"))
        action = menu.exec_(event.screenPos())
        if action == delete_action:
            # Si c'est un nœud, sélectionner aussi ses connecteurs
            if hasattr(self, 'model_element') and isinstance(self.model_element, EObject):
                items_to_delete = [self] + self.outgoing_connectors + self.incoming_connectors
                self.main_window.delete_selected_items(items_to_delete)
            else:
                self.main_window.delete_selected_items([self])  # Sinon, juste l'item courant
        elif action == rename_action:
            self.old_label = self.label_item.toPlainText()  # Sauvegarder l'ancien label avant édition
            self.label_item.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.label_item.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.main_window.delete_selected_items()  # Appel sur MainWindow
        else:
            super().keyPressEvent(event)

    def delete_self(self):
        self.main_window.delete_selected_items()  # Appel sur MainWindow

    def delete_connector(self):
        self.main_window.delete_selected_items()  # Appel sur MainWindow


    #************************************#

    def add_control_point(self, pos):
        # MODIFICATION : Pas de limite stricte, mais 5 points max suggérés
        if len(self.control_points) < 5:
            self.control_points.append(pos)
            self.update_control_point_handles()
            self.update_relative_t()
            self.control_points_updated_signal.emit(
                self.source.model_element.id,
                self.target.model_element.id,
                self.conn_type,
                self.control_points
            )

    # -------------------
    def remove_control_point(self, index):
        if 0 <= index < len(self.control_points):
            self.control_points.pop(index)
            self.update_control_point_handles()
            self.update_relative_t()
            self.control_points_updated_signal.emit(
                self.source.model_element.id,
                self.target.model_element.id,
                self.conn_type,
                self.control_points
            )

    # -------------------

    def update_control_point_handles(self):
        for handle in self.control_point_handles:
            if handle.scene():
                handle.scene().removeItem(handle)
        self.control_point_handles.clear()
        if self.scene() is None:
            print("Avertissement : Aucune scène associée, poignées non ajoutées.")
            return
        for i, _ in enumerate(self.control_points):
            handle = ControlPointHandle(self, i)
            self.scene().addItem(handle)
            self.control_point_handles.append(handle)

    # -------------------
    """
    def on_label_focus_out(self, event):
        old_label = self.label_item.toPlainText()
        self.label_item.setTextInteractionFlags(Qt.NoTextInteraction)
        new_label = self.label_item.toPlainText()  # Note : toPlainText() est déjà appelé ici
        if old_label != new_label:  # Vérifier si le label a changé
            self.setToolTip(new_label)
            self.update_label_position()
            old_state = {'label': old_label, 'type': self.connector_type, 'control_points': self.control_points.copy()}
            new_state = {'label': new_label, 'type': self.connector_type, 'control_points': self.control_points.copy()}
            self.main_window.execute_command(ModifyConnectorCommand(self.main_window, self, old_state, new_state))
            self.connector_label_updated_signal.emit(
                self.source.model_element.id,
                self.target.model_element.id,
                self.conn_type,
                new_label
            )
        super(QGraphicsTextItem, self.label_item).focusOutEvent(event)
    """
    

    # -------------------
    def on_label_focus_out(self, event):
        new_label = self.label_item.toPlainText()  # Obtenir le nouveau texte après édition
        print(f"on_label_focus_out: old_label='{self.old_label}', new_label='{new_label}'")  # Débogage
        if self.old_label != new_label:  # Vérifier si le label a changé
            print(f"Label modifié, enregistrant commande: old='{self.old_label}', new='{new_label}'")
            self.label_item.setTextInteractionFlags(Qt.NoTextInteraction)
            self.setToolTip(new_label)
            self.update_label_position()
            old_state = {'label': self.old_label, 'type': self.connector_type, 'control_points': self.control_points.copy()}
            new_state = {'label': new_label, 'type': self.connector_type, 'control_points': self.control_points.copy()}
            try:
                self.main_window.execute_command(ModifyConnectorCommand(self.main_window, self, old_state, new_state))
                print("Commande ModifyConnectorCommand exécutée avec succès")
            except Exception as e:
                print(f"Erreur lors de l'exécution de la commande : {e}")
            self.connector_label_updated_signal.emit(
                self.source.model_element.id,
                self.target.model_element.id,
                self.conn_type,
                new_label
            )
            self.old_label = new_label  # Mettre à jour l'ancien label pour les prochaines éditions
        else:
            self.label_item.setTextInteractionFlags(Qt.NoTextInteraction)
            print("Aucun changement de label détecté, pas de commande enregistrée")
        super(QGraphicsTextItem, self.label_item).focusOutEvent(event)

    # -------------------
    def update_label_position(self):
        if not self.source or not self.target or not hasattr(self, 'label_item'):
            return
        path = self.path()
        mid_point = path.pointAtPercent(0.5)
        label_rect = self.label_item.boundingRect()
        self.label_item.setPos(mid_point - QPointF(label_rect.width() / 2, label_rect.height() / 2))

    # -------------------
    def mouseDoubleClickEvent(self, event):
        self.old_label = self.label_item.toPlainText()  # Sauvegarder l'ancien label avant édition
        self.label_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.label_item.setFocus()
        super().mouseDoubleClickEvent(event)

    # -------------------
    def set_connector_type(self, connector_type):
        old_type = self.connector_type
        old_control_points = self.control_points.copy()
        self.connector_type = connector_type
        self.style["type"] = connector_type
        if connector_type in ["curved", "rounded", "orthogonal"]:
            self.control_points = self.generate_control_points()
            self.control_points_updated_signal.emit(
                self.source.model_element.id,
                self.target.model_element.id,
                self.conn_type,
                self.control_points
            )
        else:
            self.control_points = []
        old_state = {'label': self.label_item.toPlainText(), 'type': old_type, 'control_points': old_control_points}
        new_state = {'label': self.label_item.toPlainText(), 'type': connector_type, 'control_points': self.control_points.copy()}
        self.main_window.execute_command(ModifyConnectorCommand(self.main_window, self, old_state, new_state))
        self.connector_type_updated_signal.emit(
            self.source.model_element.id,
            self.target.model_element.id,
            self.conn_type,
            connector_type
        )
        self.update_path()

