from PySide6.QtWidgets import QGraphicsView, QMessageBox, QGraphicsTextItem, QGraphicsItem, QGraphicsScene
from PySide6.QtCore import Qt, QPointF, Signal, QMimeData
from PySide6.QtGui import QCursor, QPainter, QTransform, QPen, QBrush, QColor, Qt
from items.agent_item import AgentItem
from items.resource_item import ResourceItem
from items.process_item import ProcessItem
from items.parameter_item import ParameterItem
from items.connector_item import ConnectorItem


class SocioEcosystemView(QGraphicsView):
    itemDropped = Signal(str, QPointF)
    itemMoved = Signal()
    itemAdded = Signal()
    process_deleted = Signal()

    # Constantes pour le contrôle du zoom
    ZOOM_FACTOR = 1.2  # Facteur par lequel le zoom augmente/diminue
    ZOOM_MIN = 0.5     # Zoom minimum (50%)
    ZOOM_MAX = 5.0     # Zoom maximum (500%)

    def __init__(self, main_window, parent=None): 
        super().__init__(parent)
        self.main_window = main_window # On stocke la référence
        self.setRenderHint(QPainter.Antialiasing)
        self.setMouseTracking(True)
        
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        # ----------- grid background
        self.grid_enabled = self.main_window.snap_to_grid 
        self.setRenderHint(QPainter.Antialiasing)


    ####**************************************####

    def drawBackground(self, painter, rect):
        """Dessine l'arrière-plan de la vue, y compris la grille si elle est activée."""
        
        # Appeler la méthode parente pour le dessin par défaut (souvent un fond blanc/gris)
        super().drawBackground(painter, rect)

        if not self.grid_enabled:
            return

        # Récupération de la taille de la grille depuis MainWindow
        grid_size = self.main_window.grid_size

        # 1. Définir le style de la grille
        pen = QPen(QColor(200, 200, 200), 1) # Couleur gris clair, épaisseur 1
        pen.setStyle(Qt.DotLine)             # Style de ligne pointillée
        painter.setPen(pen)

        # 2. Calculer les bornes de dessin
        # Nous devons dessiner uniquement dans la zone visible par la vue (rect)
        
        # Trouver le point de départ ajusté à la grille
        left = int(rect.left())
        top = int(rect.top())
        
        # 3. Dessiner les lignes Verticales
        x = left - (left % grid_size)
        while x < rect.right():
            # Dessine une ligne verticale de 'top' à 'bottom' dans la zone visible
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += grid_size

        # 4. Dessiner les lignes Horizontales
        y = top - (top % grid_size)
        while y < rect.bottom():
            # Dessine une ligne horizontale de 'left' à 'right' dans la zone visible
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += grid_size
            
        # 5. Dessiner l'axe principal (optionnel, pour meilleure référence visuelle)
        # Si vous voulez une ligne plus foncée pour l'axe (0, 0)
        main_pen = QPen(QColor(150, 150, 150), 1)
        # painter.setPen(main_pen)
        # painter.drawLine(rect.left(), 0, rect.right(), 0) # Axe X
        # painter.drawLine(0, rect.top(), 0, rect.bottom()) # Axe Y

    ####**************************************####

    def zoom_in(self):
        """Augmente le niveau de zoom."""
        # Récupère la transformation actuelle
        current_scale = self.transform().m11()
        
        # Calcule la nouvelle échelle
        new_scale = current_scale * self.ZOOM_FACTOR
        
        if new_scale <= self.ZOOM_MAX:
            # Applique la nouvelle transformation (mise à l'échelle)
            self.scale(self.ZOOM_FACTOR, self.ZOOM_FACTOR)
            self.main_window.statusBar().showMessage(f"Zoom : {new_scale:.0%} (Max : {self.ZOOM_MAX:.0%})")
        else:
            self.main_window.statusBar().showMessage(f"Zoom maximum ({self.ZOOM_MAX:.0%}) atteint.", 2000)

    def zoom_out(self):
        """Diminue le niveau de zoom."""
        current_scale = self.transform().m11()
        new_scale = current_scale / self.ZOOM_FACTOR
        
        if new_scale >= self.ZOOM_MIN:
            # Applique la transformation inverse
            self.scale(1.0 / self.ZOOM_FACTOR, 1.0 / self.ZOOM_FACTOR)
            self.main_window.statusBar().showMessage(f"Zoom : {new_scale:.0%} (Min : {self.ZOOM_MIN:.0%})")
        else:
            self.main_window.statusBar().showMessage(f"Zoom minimum ({self.ZOOM_MIN:.0%}) atteint.", 2000)
    
    def fit_in_view(self):
        """Ajuste l'ensemble du contenu de la scène à la zone visible de la vue."""
        if self.scene().items():
            # Réinitialise toute rotation ou mise à l'échelle avant d'ajuster
            self.setTransform(QTransform())
            
            # Obtient le rectangle englobant de tous les éléments de la scène
            rect = self.scene().itemsBoundingRect()
            
            # Utilise fitInView pour ajuster ce rectangle à la vue
            # Qt.KeepAspectRatio garantit que les proportions sont maintenues
            self.fitInView(rect, Qt.KeepAspectRatio)
            self.main_window.statusBar().showMessage("Diagramme ajusté à la fenêtre.", 2000)
        else:
            self.main_window.statusBar().showMessage("La scène est vide, impossible d'ajuster.", 2000)

        
    ####**************************************####
  

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
            # Utiliser le curseur Copy ou Move
            self.setCursor(Qt.CopyCursor) 
        else:
            super().dragEnterEvent(event)

     ####**************************************####

    def dragMoveEvent(self, event):
        event.acceptProposedAction()
        self.setCursor(Qt.ArrowCursor) 


    def dropEvent(self, event):
        drop_type = event.mimeData().text()
        position = self.mapToScene(event.pos()) # Mappe la position de l'événement à la scène

        # Émet le signal approprié en fonction du type glissé
        self.itemDropped.emit(drop_type, position)
        event.acceptProposedAction()
        self.setCursor(Qt.ArrowCursor)


    ####**************************************####

    def mousePressEvent(self, event):
        try:
            item = self.itemAt(event.pos())

            # S'assurer que l'on manipule l'élément parent s'il y a un clic sur un enfant
            if item and not hasattr(item, 'model_element') and item.parentItem():
                item = item.parentItem()

            # S'assurer que l'on manipule l'élément parent si un enfant non movable est cliqué
            if item and not item.flags() & QGraphicsItem.ItemIsMovable:
                parent = item.parentItem()
                if parent and parent.flags() & QGraphicsItem.ItemIsMovable:
                    item = parent

            # Annuler si on clique sur un connecteur
            # ... (le code existant ici est correct pour l'annulation simple) ...
            if isinstance(item, ConnectorItem):
                self.main_window.connection_mode = None
                self.main_window.connection_source = None
                self.main_window.setCursor(QCursor(Qt.ArrowCursor))
                self.main_window.statusBar().showMessage("Connecteur sélectionné. Mode de création annulé.")
                super().mousePressEvent(event)
                return

            # Gestion des clics gauche
            if event.button() == Qt.LeftButton:
                if self.main_window.connection_mode:
                    
                    # Définir si on est en mode GÉNÉRIQUE ou SPÉCIFIQUE
                    is_generic_mode = (self.main_window.connection_mode == 'active_generic')
                    
                    if self.main_window.connection_source is None:
                        # Premier clic : sélection de la source
                        if item and hasattr(item, 'model_element'):
                            source = item.model_element
                            mode = self.main_window.connection_mode
                            
                            # Ligne de débogage à ajouter :
                            #print(f"Début de la validation. Mode de connexion: '{mode}'")

                            # MODIFICATION DU PREMIER CLIC : Permet tout en mode générique
                            can_be_source = (is_generic_mode or self.main_window.model_manager.validate_source(source.eClass.name, mode))
                            
                            if can_be_source:
                                self.main_window.connection_source = item
                                self.main_window.statusBar().showMessage(f"Source '{item.text_item.toPlainText()}' sélectionnée. Cliquez sur la cible.")
                                self.setCursor(QCursor(Qt.CrossCursor))
                            else:
                                # Source invalide pour un mode spécifique donné, on annule
                                self.main_window.update_connection_state(None) # Utilisation de la nouvelle fonction harmonisée
                                self.main_window.statusBar().showMessage("Type de source invalide pour cette connexion spécifique.")
                        else:
                            self.main_window.update_connection_state(None) # Utilisation de la nouvelle fonction harmonisée
                            self.main_window.statusBar().showMessage("Sélection de la source annulée (clic sur un espace vide).")
                    else:
                        # Deuxième clic : sélection de la cible
                        if item and hasattr(item, 'model_element') and item != self.main_window.connection_source:
                            
                            if is_generic_mode:
                                # 🚨 MODIFICATION DU DEUXIÈME CLIC : Mode GÉNÉRIQUE -> Ouvre le dialogue de sélection
                                self.main_window.initiate_link_type_selection(self.main_window.connection_source, item)
                                # Le dialogue s'occupe de la validation, création et réinitialisation de l'état
                                
                            else:
                                # Mode SPÉCIFIQUE (vient de la palette) -> Validation et création directes
                                source = self.main_window.connection_source.model_element
                                target = item.model_element
                                mode = self.main_window.connection_mode # mode est bien le type de lien ici
                                
                                is_valid, message = self.main_window.model_manager.validate_connection(source, target, mode)
                                
                                if is_valid:
                                    self.main_window.create_connector_from_ui(self.main_window.connection_source, item, mode)
                                else:
                                    self.main_window.statusBar().showMessage(message)
                                    
                                # Réinitialisation après création (mode spécifique)
                                self.main_window.update_connection_state(None) # Utilisation de la nouvelle fonction harmonisée
                        else:
                            self.main_window.statusBar().showMessage("Cible de connexion invalide ou même élément que la source. Mode connexion annulé.")
                            self.main_window.update_connection_state(None) # Utilisation de la nouvelle fonction harmonisée
                            
                    # Consomme l'événement (pour bloquer le déplacement et la sélection par défaut)
                    event.accept() 
                else:
                    # Si pas de mode de connexion actif
                    super().mousePressEvent(event)
            else:
                # Clic sur un bouton autre que le gauche (ex: clic droit pour menu contextuel)
                # On annule le mode de connexion si actif, mais on laisse l'événement se propager
                if self.main_window.connection_mode:
                    self.main_window.update_connection_state(None)
                    self.main_window.statusBar().showMessage("Mode connexion annulé (clic droit ou autre).", 2000)
                    
                super().mousePressEvent(event)

        except Exception as e:
            print(f"❌ ERREUR mousePressEvent: {e}")
            # Toujours appeler le parent
            super().mousePressEvent(event)


  ####**************************************####   

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Correction : utiliser self.mapToScene()
            item = self.itemAt(event.pos())
            if item:
                if hasattr(item, 'model_element'):
                    x = item.pos().x()
                    y = item.pos().y()
                    self.main_window.model_manager.update_element_position(item.model_element, x, y)
                self.itemMoved.emit()
        super().mouseReleaseEvent(event)


    ####**************************************####


    

    ####**************************************####