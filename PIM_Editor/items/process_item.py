# process_item.py
from PySide6.QtWidgets import QGraphicsTextItem, QMenu
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QPainterPath
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
import math


import sys
from pathlib import Path
# Configuration du path pour les modules locaux
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
from baseItem import BaseItem
from dialogs.processdialog import ProcessDialog


class ProcessItem(BaseItem):
    # Signaux spécifiques aux Processes
    process_updated = Signal()
    process_deleted = Signal()

    DEFAULT_WIDTH = 160.0   # Au lieu de 120.0
    DEFAULT_HEIGHT = 90.0   # Au lieu de 60.0
    MIN_WIDTH = 100.0       # Au lieu de 80.0  
    MIN_HEIGHT = 60.0       # Au lieu de 40.0
    
    # Constantes spécifiques aux Processes    
    PROCESS_TYPE_COLORS = {
        "TransformationProcess": "#3249CD",  # Vert lime pour transformation
        "MovementProcess": "#7B8ACE"    # Or pour mouvement
    }


    def __init__(self, model_element, main_window, parent=None):
        # Appel au constructeur parent
        super().__init__(model_element, main_window, parent)
        self.model_element = model_element  # Garder une référence spécifique
        
        # Vérification que le processus est d'un type concret
        process_type = self.model_element.eClass.name
        if process_type not in self.PROCESS_TYPE_COLORS:
            raise ValueError(f"Type de processus non supporté: {process_type}")
        
        
        # Mise à jour de la couleur selon le type de processus
        self._update_color_by_type()
        
        # Mise à jour du texte d'affichage
        self._update_display_text()



    # -----------
    def shape(self):
        """
        Redéfinit la forme de sélection pour correspondre à l'hexagone.
        """
        path = QPainterPath()
        rect = self.rect()
        center_x = rect.center().x()
        center_y = rect.center().y()
        width = rect.width()
        height = rect.height()
        
        # Même calcul que _draw_hexagon mais pour la sélection
        hex_width = width * 0.85
        hex_height = height * 0.85
        
        # Créer le polygone de l'hexagone
        points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.radians(angle_deg)
            x = center_x + (hex_width / 2) * math.cos(angle_rad)
            y = center_y + (hex_height / 2) * math.sin(angle_rad)
            points.append(QPointF(x, y))
        
        # Construire le path de sélection
        path.moveTo(points[0])
        for point in points[1:]:
            path.lineTo(point)
        path.closeSubpath()
        
        return path

    def boundingRect(self):
        """
        Retourne le rectangle englobant (inchangé).
        """
        return super().boundingRect()

    def contains(self, point):
        """
        Vérifie si un point est dans l'hexagone.
        """
        return self.shape().contains(point)
    

    def mousePressEvent(self, event):
        """Gère le clic souris pour le redimensionnement de l'hexagone."""
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            rect = self.rect()
            
            # Calculer les zones de redimensionnement sur l'hexagone
            hex_rect = QRectF(
                rect.x() + rect.width() * 0.075,  # Décalage pour l'hexagone
                rect.y() + rect.height() * 0.075,
                rect.width() * 0.85,
                rect.height() * 0.85
            )
            
            # Vérifier les bords de l'hexagone pour le redimensionnement
            margin = 8.0
            self.resizing = None
            
            # Zones de redimensionnement sur l'hexagone
            if abs(pos.x() - hex_rect.left()) < margin:
                self.resizing = 'left'
            elif abs(pos.x() - hex_rect.right()) < margin:
                self.resizing = 'right'
            elif abs(pos.y() - hex_rect.top()) < margin:
                self.resizing = 'top'
            elif abs(pos.y() - hex_rect.bottom()) < margin:
                self.resizing = 'bottom'
            
            if self.resizing:
                self.start_resize_pos = event.scenePos()
                self.start_rect = rect
                event.accept()
                return
        
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Gère le déplacement souris pour le redimensionnement de l'hexagone."""
        if self.resizing:
            # Logique de redimensionnement adaptée à l'hexagone
            current_pos = event.scenePos()
            delta = current_pos - self.start_resize_pos
            
            new_rect = QRectF(self.start_rect)
            
            if self.resizing == 'left':
                new_rect.setLeft(self.start_rect.left() + delta.x())
            elif self.resizing == 'right':
                new_rect.setRight(self.start_rect.right() + delta.x())
            elif self.resizing == 'top':
                new_rect.setTop(self.start_rect.top() + delta.y())
            elif self.resizing == 'bottom':
                new_rect.setBottom(self.start_rect.bottom() + delta.y())
            
            # Appliquer les contraintes de taille minimale
            if new_rect.width() >= self.MIN_WIDTH and new_rect.height() >= self.MIN_HEIGHT:
                self.setRect(new_rect)
                self.update_text_position()
                self.update()
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    # -----------

    def _get_display_text(self):
        """Retourne le texte à afficher pour le processus"""
        process_type = self._get_process_type_display_name()
        equation = getattr(self.model_element, 'equation', '')
        pseudo_code = getattr(self.model_element, 'pseudoCode', '')
        
        # Texte principal avec type
        display_text = f"{self.model_element.name}\n({process_type})"
        
        '''
        # boite avec plus d'infos
        # Informations spécifiques selon le type
        if self.model_element.eClass.name == "MovementProcess":
            source = getattr(self.model_element, 'source', None)
            destination = getattr(self.model_element, 'destination', None)
            if source and destination:
                display_text += f"\n{getattr(source, 'name', '?')} → {getattr(destination, 'name', '?')}"
        
        # Ajouter équation si présente
        if equation:
            display_text += f"\nÉq: {equation[:15]}{'...' if len(equation) > 15 else ''}"
        '''
         
        return display_text

    def _get_process_type_display_name(self):
        """Retourne le nom d'affichage du type de processus"""
        process_type = self.model_element.eClass.name
        type_mapping = {
            "TransformationProcess": "Transformation", 
            "MovementProcess": "Mouvement"
        }
        return type_mapping.get(process_type, "Processus")

    def _update_color_by_type(self):
        """Met à jour la couleur selon le type de processus"""
        process_type = self.model_element.eClass.name
        color_hex = self.PROCESS_TYPE_COLORS.get(process_type, "#87CEEB")
        self.setBrush(QBrush(QColor(color_hex)))

    def _open_edit_dialog(self):
        """Ouvre le dialogue d'édition spécifique aux Processes"""
        scene = self.scene()
        if not scene or not scene.views():
            return
            
        main_window = scene.views()[0].main_window
        model_manager = main_window.model_manager
        current_model = model_manager.current_model

        # 1. Processes existants (validation d'unicité)
        existing_processes = current_model.processes if current_model else []
        existing_ids = [process.id for process in existing_processes if process.id != self.model_element.id]

        # 2. AGENTS - Conforme au métamodèle
        current_agents = current_model.agents if current_model else []

        # 3. RESSOURCES - Conforme au métamodèle
        current_resources = [
            prop for prop in current_model.properties 
            if hasattr(prop, 'eClass') and prop.eClass.name == 'Resource'
        ] if current_model else []

        # 4. PARAMÈTRES - Conforme au métamodèle
        current_parameters = [
            prop for prop in current_model.properties 
            if hasattr(prop, 'eClass') and prop.eClass.name == 'Parameter'
        ] if current_model else []

        # 5. ENTITÉS CONNECTÉES (relations actuelles)
        current_relations = {
            'subjects': getattr(self.model_element, 'subjects', None),
            'object': getattr(self.model_element, 'object', None),
            'involvedResources': list(getattr(self.model_element, 'involvedResources', [])),
            'dependsOnParameters': list(getattr(self.model_element, 'dependsOnParameters', [])),
            'affectsResources': list(getattr(self.model_element, 'affectsResources', [])),
            'source': getattr(self.model_element, 'source', None),
            'destination': getattr(self.model_element, 'destination', None)
        }

        dialog = ProcessDialog(
            process=self.model_element,
            parent=main_window,
            existing_ids=existing_ids,
            current_agents=current_agents,          # Tous les agents
            current_resources=current_resources,    # Resources depuis properties
            current_parameters=current_parameters,  # Parameters depuis properties
            connected_entities=current_relations    # Relations existantes
        )
        
        if dialog.exec():
            self._update_from_dialog_data(dialog.get_data())

    def _update_from_dialog_data(self, data):
        """Met à jour le processus à partir des données du dialogue"""
        # Mise à jour des attributs de base (NamedElement)
        self.model_element.id = data["id"]
        self.model_element.name = data["name"]
        self.model_element.description = data.get("description", "")
        self.model_element.comment = data.get("comment", "")
        
        # Mise à jour des attributs spécifiques à Process
        self.model_element.equation = data.get("equation", "")
        self.model_element.pseudoCode = data.get("pseudoCode", "")
        
        # Mise à jour des références communes
        self.model_element.involvedResources = data.get("involvedResources", [])
        self.model_element.dependsOnParameters = data.get("dependsOnParameters", [])
        
        # Mise à jour des attributs spécifiques au type
        process_type = data.get("process_type", self.model_element.eClass.name)
        
        if process_type == "TransformationProcess":
            # Attributs spécifiques aux TransformationProcess
            transformation_type = data.get("transformationType", "Production")
            self.model_element.transformationType = transformation_type
            self.model_element.affectsResources = data.get("affectsResources", [])
            
        elif process_type == "MovementProcess":
            # Pour MovementProcess, source et destination sont des lieux (agents)
            # qui peuvent être différents des sujets/objets
            source_agent = data.get("source")
            destination_agent = data.get("destination")
            
            if source_agent:
                self.model_element.source = source_agent
            if destination_agent:
                self.model_element.destination = destination_agent
            
            # Pas de vérification de cohérence stricte car :
            # - Source peut être ou ne pas être le sujet
            # - Destination peut être ou ne pas être l'objet
            # Exemple 1: Éleveur(sujet) move Troupeaux(objet) de Étable(source) à Champs(destination)
            # Exemple 2: Agro-éleveur(sujet) transporte Foins(ressource) de Champs(source) à Étable(destination)
        
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
        self.process_updated.emit()
        
        # Mise à jour des connecteurs
        self._update_connectors()

    
    '''
    def paint(self, painter, option, widget=None):
        """Dessin personnalisé pour les processus"""
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        # Utiliser la couleur actuelle du processus
        brush = self.brush()
        pen = self.SELECTED_PEN if self.isSelected() else self.NORMAL_PEN
        
        painter.setBrush(brush)
        painter.setPen(pen)
        
        # Forme hexagonale pour les processus (plus distinctive)
        self._draw_hexagon(painter, rect)
        
        # Ajouter un indicateur visuel pour le type de processus
        self._paint_process_indicator(painter, rect)
    ''' 

    def paint(self, painter, option, widget=None):
        """Dessin personnalisé pour les processus avec indicateurs de redimensionnement."""
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        # Utiliser la couleur actuelle
        brush = self.brush()
        pen = self.SELECTED_PEN if self.isSelected() else self.NORMAL_PEN
        
        painter.setBrush(brush)
        painter.setPen(pen)
        
        # Dessiner l'hexagone
        self._draw_hexagon(painter, rect)
        
        # 🔥 OPTIONNEL : Afficher les zones de redimensionnement en mode debug
        if self.isSelected() and False:  # Mettre à True pour debug
            debug_pen = QPen(Qt.red, 1, Qt.DashLine)
            painter.setPen(debug_pen)
            painter.setBrush(Qt.NoBrush)
            
            hex_rect = QRectF(
                rect.x() + rect.width() * 0.075,
                rect.y() + rect.height() * 0.075, 
                rect.width() * 0.85,
                rect.height() * 0.85
            )
            painter.drawRect(hex_rect)

   
    
    def _draw_hexagon(self, painter, rect):
        """Dessine une forme hexagonale pour le processus"""
        center_x = rect.center().x()
        center_y = rect.center().y()
        width = rect.width()
        height = rect.height()
        
        hex_width = width * 0.85  # 85% de la largeur au lieu de 80%
        hex_height = height * 0.85  # 85% de la hauteur au lieu de 80%
        
        # Calcul des points de l'hexagone
        points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.radians(angle_deg)
            x = center_x + (hex_width / 2) * math.cos(angle_rad)  
            y = center_y + (hex_height / 2) * math.sin(angle_rad) 
            points.append(QPointF(x, y))
        
        # Dessiner l'hexagone
        painter.drawPolygon(points)

    def _paint_process_indicator(self, painter, rect):
        """Ajoute un indicateur visuel pour le type de processus"""
        indicator_size = 10
        indicator_margin = 4
        
        # Position en haut à gauche
        indicator_rect = QRectF(
            rect.left() + indicator_margin,
            rect.top() + indicator_margin,
            indicator_size,
            indicator_size
        )
        
        # Symbole selon le type de processus
        process_type = self.model_element.eClass.name
        
        painter.setPen(QPen(Qt.black, 1))
        
        if process_type == "TransformationProcess":
            # Flèche circulaire pour transformation
            painter.drawEllipse(indicator_rect)
            center = indicator_rect.center()
            painter.drawLine(center.x() - 3, center.y(), center.x() + 3, center.y())
            painter.drawLine(center.x(), center.y() - 3, center.x(), center.y() + 3)
            
        elif process_type == "MovementProcess":
            # Double flèche pour mouvement (↔)
            center = indicator_rect.center()
            # Ligne horizontale
            painter.drawLine(center.x() - 4, center.y(), center.x() + 4, center.y())
            # Flèche gauche
            painter.drawLine(center.x() - 4, center.y(), center.x() - 2, center.y() - 2)
            painter.drawLine(center.x() - 4, center.y(), center.x() - 2, center.y() + 2)
            # Flèche droite
            painter.drawLine(center.x() + 4, center.y(), center.x() + 2, center.y() - 2)
            painter.drawLine(center.x() + 4, center.y(), center.x() + 2, center.y() + 2)

    def contextMenuEvent(self, event):
        """Menu contextuel spécifique aux processus"""
        menu = QMenu()
        
        # Actions standard
        edit_action = menu.addAction("Éditer le Processus")
        delete_action = menu.addAction("Supprimer le Processus")
        menu.addSeparator()
        
        # Actions spécifiques aux processus
        show_connections_action = menu.addAction("Afficher les Connexions")
        show_equation_action = menu.addAction("Afficher l'Équation")
        
        # Actions spécifiques au type
        process_type = self.model_element.eClass.name
        if process_type == "MovementProcess":
            menu.addSeparator()
            show_movement_details_action = menu.addAction("Détails du Mouvement")
        
        action = menu.exec(event.screenPos())
        
        if action == edit_action:
            self._open_edit_dialog()
        elif action == delete_action:
            self._delete_item()
        elif action == show_connections_action:
            self._show_connections()
        elif action == show_equation_action:
            self._show_equation()
        elif process_type == "MovementProcess" and action == show_movement_details_action:
            self._show_movement_details()

    def _show_connections(self):
        """Affiche les connexions du processus"""
        print(f"Connexions du processus {self.model_element.name} ({self.model_element.eClass.name}):")
        
        # Sujets (agents qui mettent en œuvre)
        subjects = getattr(self.model_element, 'subjects', None)
        print(f"  - Sujets (acteurs): {[agent.name for agent in subjects]}")
        
        # Objet (agent qui subit)
        process_object = getattr(self.model_element, 'object',  [])
        print(f"  - Objets (subit): {getattr(process_object, 'name', 'Aucun')}")
        
        # Ressources impliquées
        involved_resources = getattr(self.model_element, 'involvedResources', [])
        print(f"  - Ressources impliquées: {[res.name for res in involved_resources]}")
        
        # Paramètres dépendants
        depends_parameters = getattr(self.model_element, 'dependsOnParameters', [])
        print(f"  - Paramètres dépendants: {[param.name for param in depends_parameters]}")
        
        # Connexions spécifiques au type
        process_type = self.model_element.eClass.name
        if process_type == "TransformationProcess":
            affects_resources = getattr(self.model_element, 'affectsResources', [])
            transformation_type = getattr(getattr(self.model_element, 'transformationType', None), 'name', 'Non défini')
            print(f"  - Ressources affectées: {[res.name for res in affects_resources]}")
            print(f"  - Type de transformation: {transformation_type}")
            
        elif process_type == "MovementProcess":
            source = getattr(self.model_element, 'source', None)
            destination = getattr(self.model_element, 'destination', None)
            print(f"  - Source (lieu origine): {getattr(source, 'name', 'Non connecté')}")
            print(f"  - Destination (lieu arrivée): {getattr(destination, 'name', 'Non connecté')}")

    def _show_movement_details(self):
        """Affiche les détails spécifiques du mouvement avec sémantique correcte"""
        if self.model_element.eClass.name != "MovementProcess":
            return
            
        subjects = getattr(self.model_element, 'subjects', [])
        process_object = getattr(self.model_element, 'object', None)
        involved_resources = getattr(self.model_element, 'involvedResources', [])
        source = getattr(self.model_element, 'source', None)
        destination = getattr(self.model_element, 'destination', None)
        
        print(f"=== Détails du Mouvement: {self.model_element.name} ===")
        
        # Sémantique selon les exemples fournis
        print("\n🎭 RÔLES:")
        print(f"  • Acteur(s): {[agent.name for agent in subjects]} (met en œuvre le mouvement)")
        
        if process_object:
            print(f"  • Objet déplacé: {process_object.name} (subit le mouvement)")
        
        if involved_resources:
            print(f"  • Ressource(s) transportée(s): {[res.name for res in involved_resources]}")
        
        print("\n📍 TRAJECTOIRE:")
        print(f"  • Départ: {getattr(source, 'name', 'Non spécifié')}")
        print(f"  • Arrivée: {getattr(destination, 'name', 'Non spécifié')}")
        
        # Exemples de patterns détectés
        print("\n🔍 INTERPRÉTATION:")
        if process_object and isinstance(process_object, type(subjects[0]) if subjects else None):
            # Pattern: Déplacement d'un agent (Exemple 1)
            print("  → Type: Déplacement d'agent")
            if subjects and process_object in subjects:
                print("  → Note: L'agent se déplace lui-même")
            else:
                print(f"  → Note: {subjects[0].name if subjects else 'Acteur'} déplace {process_object.name}")
        elif involved_resources:
            # Pattern: Transport de ressources (Exemple 2)
            print("  → Type: Transport de ressources")
            print(f"  → Ressources: {[res.name for res in involved_resources]}")
        else:
            print("  → Type: Mouvement non spécifié")

    def _show_equation(self):
        """Affiche l'équation du processus"""
        equation = getattr(self.model_element, 'equation', '')
        pseudo_code = getattr(self.model_element, 'pseudoCode', '')
        
        if equation:
            print(f"Équation du processus {self.model_element.name}: {equation}")
        elif pseudo_code:
            print(f"Pseudo-code du processus {self.model_element.name}: {pseudo_code}")
        else:
            print(f"Le processus {self.model_element.name} n'a pas d'équation ni de pseudo-code défini.")

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
        """Retourne les éléments liés à ce processus"""
        related = []
        
        # Sujets (agents acteurs)
        process_subject = getattr(self.model_element, 'subjects', None)
        if process_subject:
            related.append(('subject', process_subject))
            
        # Objet (agent qui subit)
        process_object = getattr(self.model_element, 'object', None)
        if process_object:
            related.append(('object', process_object))
            
        # Ressources impliquées
        for resource in getattr(self.model_element, 'involvedResources', []):
            related.append(('involved_resource', resource))
            
        # Paramètres dépendants
        for parameter in getattr(self.model_element, 'dependsOnParameters', []):
            related.append(('depends_parameter', parameter))
            
        # Connexions spécifiques au type
        process_type = self.model_element.eClass.name
        if process_type == "TransformationProcess":
            # Ressources affectées
            for resource in getattr(self.model_element, 'affectsResources', []):
                related.append(('affects_resource', resource))
                
        elif process_type == "MovementProcess":
            # Source et destination (lieux)
            source = getattr(self.model_element, 'source', None)
            destination = getattr(self.model_element, 'destination', None)
            if source:
                related.append(('source_location', source))
            if destination:
                related.append(('destination_location', destination))
                
        return related

    def _delete_item(self):
        """Suppression spécifique du processus"""
        if self.main_window and self.main_window.view.scene():
            self.main_window.delete_selected_items([self])
            self.process_deleted.emit()