from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, 
    QTabWidget, QWidget, QVBoxLayout, QGraphicsScene, QGraphicsView,
    QToolBar, QDockWidget, QTreeWidget, QTreeWidgetItem, QPushButton, QFrame,
    QGroupBox, QStatusBar, QGraphicsItem, QGraphicsTextItem, QMenu, QGraphicsLineItem, 
    QDialog, QToolButton, QInputDialog, QComboBox, QCheckBox, QSpinBox, QLabel,
    QHBoxLayout
)
from PySide6.QtCore import (
    Qt, QPointF, QPoint, QMimeData, Signal, 
    QSize, QRectF, QSizeF, QMarginsF, QByteArray,
    QMimeData, QByteArray
)
from PySide6.QtGui import (
    QAction, QPainter, QDrag, QPixmap, QColor, 
    QCursor, QBrush, QPen, QKeySequence, QIcon, QPixmap, 
    QImage, QPageLayout, QPageSize, QPdfWriter, QPainterPath,
    QFontDatabase, QFont, QTextDocument
)
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
import math
from math import sqrt
from pyecore.ecore import *
import fitz 
import json

import sys
from pathlib import Path
# Configuration du path pour les modules locaux
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dialogs.agentdialog import AgentDialog
from dialogs.resourcedialog import ResourceDialog
from dialogs.processdialog import ProcessDialog
from dialogs.propertydialog import ParameterDialog
from items.agent_item import AgentItem
from items.resource_item import ResourceItem
from items.process_item import ProcessItem
from items.parameter_item import ParameterItem
from items.connector_item import ConnectorItem
from modelManager.model_manager import ModelManager
from socioecosystem_view import SocioEcosystemView

from commands import (Command, AddNodeCommand, DeleteNodeCommand, 
    AddConnectorCommand, DeleteConnectorCommand,
    ModifyFieldCommand, MoveNodeCommand, DeleteItemsCommand,
    PasteItemsCommand
)

ITEM_METADATA = {
    # Types d'éléments (EClasses) - Utilisé pour les icônes et le type dans le TreeItem
    "Agent": {"label_prefix": "", "icon": "agent.png"},
    "Resource": {"label_prefix": "", "icon": "resource.png"},
    "TransformationProcess": {"label_prefix": "", "icon": "process.png"},
    "MovementProcess": {"label_prefix": "", "icon": "process.png"},
    "Parameter": {"label_prefix": "", "icon": "parameter.png"},
    
    # Collections de confinement à la racine (EFeatures)
    "agents": {"label": "👥 Agents", "icon": "agent.png"},
    
    # Relations de confinement imbriquées (EFeatures)
    "containsAgents": {"label": "Sous-Agents", "icon": "agent.png"},

    # Relations de référence (EFeatures) - Pour les nœuds enfants
    "holdsResources": {"label_prefix": "Détient (Ressource): ", "icon": "resource.png"}, 
    "isSubjectOf": {"label_prefix": "Sujet d'un (Processus): ", "icon": "process.png"},
    "isObjectOf": {"label_prefix": "Objet d'un (Processus): ", "icon": "process.png"},
    "involvedResources": {"label_prefix": "Implique (Ressource): ", "icon": "resource.png"},
    "dependsOnParameters": {"label_prefix": "Dépend de (Paramètre): ", "icon": "parameter.png"},
    "affectsResources": {"label_prefix": "Affecte (Ressource): ", "icon": "resource.png"},
}


class MainWindow(QMainWindow):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app # Stockez l'instance de l'application

        self.setWindowTitle("Éditeur Socio-Écosystème")
        self.setWindowIcon(QIcon("icons/SESIcon.png"))
        #self.resize(1200, 800)
        self.resize(1000, 600)
        self.model_manager = ModelManager("pimSocioecosytemMM.ecore")
        self.snap_to_grid = True # Gère l'activation ou la désactivation de l'alignement sur la grille
        self.grid_size = 20      # Définit la taille de la grille en pixels
        # Mapper modèle à item graphique
        self.model_to_item = {}
        
        # Gestion du mode de connexion
        self.connection_mode = None
        self.connection_source = None
        self.connection_target = None
        
              

        # Ajout des piles pour Undo/Redo
        self.undo_stack = []  # Pile des commandes à annuler
        self.redo_stack = []  # Pile des commandes annulées à rétablir
        self.max_undo_limit = 50  # Limite maximale d'actions à conserver

        # ----------------------
        self.create_actions()
         # ----------------------
        self.create_toolbars() 
         # ----------------------
        self.setup_ui()
        # ----------------------
        self.setup_global_connections()
        # ----------------------
        self.view.itemMoved.connect(self.update_connectors_on_move)
        # ----------------------
        self.clipboard = QApplication.clipboard() 
        self.clipboard_data_format = "application/x-socioecosystem-model" # Format MIME personnalisé
        # ----------------------
        self.view.scene().selectionChanged.connect(self.update_edit_actions_state)
        # ----------------------
        self.clipboard.changed.connect(self.update_paste_action_state) 
        # ----------------------
        self.model_manager.connector_types = {}
        


    def create_actions(self):
        self.new_action = QAction(QIcon.fromTheme('document-new'), "&Nouveau", self)
        self.new_action.setShortcut(QKeySequence.New) # ou "Ctrl+N"
        self.new_action.triggered.connect(self.new_model)
        self.new_action.setStatusTip("Créer un nouveau modèle")

        self.open_action = QAction(QIcon.fromTheme('document-open'), "&Ouvrir...", self)
        self.open_action.setShortcut(QKeySequence.Open) # ou "Ctrl+O"
        self.open_action.triggered.connect(self.open_model)
        self.open_action.setStatusTip("Ouvrir un modèle existant")

        self.save_action = QAction(QIcon.fromTheme('document-save'), "&Enregistrer", self)
        self.save_action.setShortcut(QKeySequence.Save) # ou "Ctrl+S"
        self.save_action.setStatusTip("Sauvegarder le modèle courant")
        self.save_action.triggered.connect(self.save_model)

        self.save_as_action = QAction(QIcon.fromTheme('document-save-as'), "Enregistrer &sous...", self)
        self.save_as_action.setShortcut(QKeySequence.SaveAs) # ou "Ctrl+Shift+S"
        self.save_as_action.triggered.connect(self.save_as_model)
        self.save_as_action.setStatusTip("Sauvegarder le modèle sous un nouveau nom")
        

        self.exit_action = QAction(QIcon.fromTheme('application-exit'), "Quitter", self)
        self.exit_action.setShortcut("Ctrl+Q") # ou "Ctrl+Q"
        self.exit_action.triggered.connect(self.app.quit)
        self.save_as_action.setStatusTip("Sauvegarder le modèle sous un nouveau nom")

        
        # Action Exporter
        self.export_action = QAction(QIcon.fromTheme('document-print-preview'), "E&xporter...", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+E")) 
        self.export_action.setStatusTip("Exporter le diagramme au format image (PNG, SVG, JPEG, PDF).")

        # -------------------------

        # Action Zoom avant
        self.zoom_in_action = QAction(QIcon.fromTheme('zoom-in'), "Zoom avant", self)
        self.zoom_in_action.setShortcut(QKeySequence("Ctrl++")) 
        self.zoom_in_action.setStatusTip("Augmenter le niveau de zoom de la scène.")

        # Action Zoom arrière
        self.zoom_out_action = QAction(QIcon.fromTheme('zoom-out'), "Zoom arrière", self)
        self.zoom_out_action.setShortcut(QKeySequence("Ctrl+-")) 
        self.zoom_out_action.setStatusTip("Diminuer le niveau de zoom de la scène.")

        # Action Ajuster à l'écran (Recommandé)
        self.fit_to_view_action = QAction(QIcon.fromTheme('zoom-fit-best'), "Ajuster à l'écran", self)
        self.fit_to_view_action.setShortcut(Qt.Key_F) 
        self.fit_to_view_action.setStatusTip("Centrer et ajuster l'ensemble du diagramme à la fenêtre.")
    
        # -------------------------

        
        self.undo_action = QAction(QIcon.fromTheme('edit-undo'), "&Annuler", self)
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.undo_action.setStatusTip("Annuler la dernière action.")
        self.undo_action.triggered.connect(self.undo_action_handler) 
        self.undo_action.setEnabled(False) # Initialement désactivé
        
        self.redo_action = QAction(QIcon.fromTheme('edit-redo'), "&Rétablir", self)
        self.redo_action.setShortcut(QKeySequence.Redo)
        self.redo_action.setStatusTip("Rétablir l'action précédemment annulée.")
        self.redo_action.triggered.connect(self.redo_action_handler) 
        self.redo_action.setEnabled(False) # Initialement désactivé
        
        

        self.cut_action = QAction(QIcon.fromTheme('edit-cut'), "&Couper", self)
        self.cut_action.setShortcut(QKeySequence.Cut)
        self.cut_action.setStatusTip("Couper l'élément sélectionné.")
        self.cut_action.triggered.connect(self.cut_selected_items) 
        self.cut_action.setEnabled(False) 

        self.copy_action = QAction(QIcon.fromTheme('edit-copy'), "&Copier", self)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.copy_action.setStatusTip("Copier l'élément sélectionné.")
        self.copy_action.triggered.connect(self.copy_selected_items) 
        self.copy_action.setEnabled(False) 

        self.paste_action = QAction(QIcon.fromTheme('edit-paste'), "&Coller", self)
        self.paste_action.setShortcut(QKeySequence.Paste)
        self.paste_action.setStatusTip("Coller l'élément du presse-papiers.")
        self.paste_action.triggered.connect(self.paste_items)
        self.paste_action.setEnabled(False)

        self.select_all_action = QAction(QIcon.fromTheme('edit-select-all'), "Sélectionner &tout", self)
        self.select_all_action.setShortcut(QKeySequence.SelectAll)
        self.select_all_action.setStatusTip("Sélectionner tous les éléments de la scène.")
        self.select_all_action.triggered.connect(self.select_all_items) 

        self.delete_action = QAction(QIcon.fromTheme('list-remove'), "Supprimer l'élément sélectionné", self)
        self.delete_action.setShortcut(Qt.Key_Delete)
        self.delete_action.triggered.connect(self.prepare_and_delete_selected_items) 
        self.delete_action.setEnabled(False)

        # -------------------------

        self.toggle_connection_mode_action = QAction(QIcon.fromTheme('stock_connect'), "Mode &Connexion", self)
        self.toggle_connection_mode_action.setCheckable(True)
        self.toggle_connection_mode_action.setShortcut(Qt.Key_L)
        self.toggle_connection_mode_action.setStatusTip("Activer/désactiver le mode de création de liens.")
        self.toggle_connection_mode_action.triggered.connect(self.toggle_connection_mode) 

        self.toggle_grid_action = QAction(QIcon.fromTheme('view-grid'), "Aligner sur la &Grille", self)
        self.toggle_grid_action.setCheckable(True)
        self.toggle_grid_action.setChecked(self.snap_to_grid) # Utilise la valeur initiale de __init__
        self.toggle_grid_action.setShortcut(Qt.Key_G)
        self.toggle_grid_action.setStatusTip("Activer/désactiver l'alignement des éléments sur la grille.")
        self.toggle_grid_action.triggered.connect(self.toggle_grid) 

        # -------------------------
    
        self.about_action = QAction(QIcon.fromTheme('help-about'), "&À propos de...", self)
        self.about_action.setStatusTip("Afficher les informations sur l'application.")
        self.about_action.triggered.connect(self.show_about_dialog) 

        # -------------------------

        self.show_palette_action = QAction("Palette d'éléments", self)
        self.show_palette_action.setCheckable(True)
        self.show_palette_action.setChecked(True) # Le dock est visible par défaut

        self.show_navigationtree_action = QAction("Arbre de navigation", self)
        self.show_navigationtree_action.setCheckable(True)
        self.show_navigationtree_action.setChecked(True) # Le dock est visible par défaut


        
        
    def create_toolbars(self):
        # Instanciation de la ToolBar
        toolbar = QToolBar("Barre d'outils principale")
        self.addToolBar(toolbar)

        # Ajout des actions de fichier
        toolbar.addAction(self.new_action)
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.open_action)
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.save_as_action)
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.export_action)
        toolbar.addSeparator()
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.copy_action)
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.cut_action)
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.paste_action)
        toolbar.addSeparator()
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.zoom_in_action)
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.zoom_out_action)
        toolbar.addSeparator()
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.fit_to_view_action)
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.select_all_action)
        toolbar.addSeparator()
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.undo_action)
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        toolbar.addSeparator()
        # --------------
        toolbar.addAction(self.exit_action)
        

        toolbar.setIconSize(QSize(16, 16)) 

        # Application du curseur à l'ensemble de la barre d'outils
        # L'endroit IDOINE
        for widget in toolbar.children():
            if isinstance(widget, QToolButton):
                widget.setCursor(Qt.PointingHandCursor)

        self.toolbar = toolbar 

    # ------------------------

    def setup_ui(self):
        self.create_menu()
        self.tool_buttons = {
            "agent": QPushButton("Agent"),
            #"resource": QPushButton("Ressource"),
            "process": QPushButton("Processus"),
            "property": QPushButton("Propriété") 
        }
        for btn in self.tool_buttons.values():
            btn.setCursor(Qt.PointingHandCursor) # Indique que c'est draggable
            btn.setCursor(Qt.OpenHandCursor) # Indique que c'est draggable
        
        # Scène et Vue
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        self.view = SocioEcosystemView(self)
        self.view.setScene(self.scene)

        # Palette
        self.palette_dock = QDockWidget("Palette d'éléments", self)
        self.palette_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable)
        self.palette_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.palette_dock.setMinimumWidth(200)

        # Lier l'action au dock
        self.show_palette_action.triggered.connect(lambda checked: self.palette_dock.setVisible(checked))
        self.palette_dock.visibilityChanged.connect(self.show_palette_action.setChecked)
        
        palette_widget = QWidget()
        palette_layout = QVBoxLayout()
        palette_layout.setAlignment(Qt.AlignTop)
        

        button_width = 160
        button_height = 40
        # Acteurs
        agent_group = QGroupBox("Agents")
        agent_layout = QVBoxLayout()
        agent_button = QPushButton("Agent")
        agent_button.setStyleSheet("""
            QPushButton {
                background-color: #FFA500;
                border: 2px solid #808080;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFB84D;
            }
        """)
        agent_button.setCursor(Qt.PointingHandCursor)
        agent_button.mousePressEvent = lambda event: self.start_drag(event, "agent")
        agent_button.setFixedSize(button_width, button_height)

        agent_layout.addWidget(agent_button)
        agent_group.setLayout(agent_layout)
        palette_layout.addWidget(agent_group)

        # Ressources
        '''
        resource_group = QGroupBox("Ressources")
        resource_layout = QVBoxLayout()
        resource_button = QPushButton("Ressource")
        resource_button.setStyleSheet("""
            QPushButton {
                background-color: #90EE90;
                border: 2px solid #808080;
                color: black;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #98FB98;
            }
        """)
        resource_button.setCursor(Qt.PointingHandCursor)
        resource_button.mousePressEvent = lambda event: self.start_drag(event, "resource")
        resource_button.setFixedSize(button_width, button_height)
        resource_layout.addWidget(resource_button)
        resource_group.setLayout(resource_layout)
        palette_layout.addWidget(resource_group)
        '''
        
        # Processus
        process_group = QGroupBox("Processus")
        process_layout = QVBoxLayout()
        process_button = QPushButton("Processus")
        process_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                border: 2px solid #0056B3;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF85C2;
            }
        """)
        process_button.setCursor(Qt.PointingHandCursor)
        process_button.mousePressEvent = lambda event: self.start_drag(event, "process")
        process_button.setFixedSize(button_width, button_height)
        process_layout.addWidget(process_button)
        process_group.setLayout(process_layout)
        palette_layout.addWidget(process_group)


        # Propriétés
        property_group = QGroupBox("Propriétés")
        property_layout = QVBoxLayout()
        property_button = QPushButton("Property")
        property_button.setStyleSheet("""
            QPushButton {
                background-color: #A9A9A9;
                border: 2px solid #808080;
                color: black;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B3B3B3;
            }
        """)
        property_button.setCursor(Qt.PointingHandCursor)
        property_button.mousePressEvent = lambda event: self.start_drag(event, "property")
        property_button.setFixedSize(button_width, button_height)
        property_layout.addWidget(property_button)
        property_group.setLayout(property_layout)
        palette_layout.addWidget(property_group)
        
        # Bouton Connexion
        connector_group = QGroupBox("Connexions")
        connector_layout = QVBoxLayout()
        connector_button = QPushButton("Connecteur")
        connector_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #000000;
                color: black;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
            }
        """)
        connector_button.setCursor(Qt.PointingHandCursor)
        connector_button.clicked.connect(self.toggle_connector_menu)
        connector_button.setFixedSize(button_width, button_height)
        connector_layout.addWidget(connector_button)
        connector_group.setLayout(connector_layout)
        palette_layout.addWidget(connector_group)

        palette_widget.setLayout(palette_layout)
        self.palette_dock.setWidget(palette_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.palette_dock)

        # Arbre de navigation
        self.tree_dock = QDockWidget("Structure du modèle", self)
        self.tree_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable)
        self.tree_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # Lier l'action au dock
        self.show_navigationtree_action.triggered.connect(lambda checked: self.tree_dock.setVisible(checked))
        self.tree_dock.visibilityChanged.connect(self.show_navigationtree_action.setChecked)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Nom", "Type"])
        self.tree_dock.setWidget(self.tree_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.tree_dock)

        # Tab Widget pour le contenu principal
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Ajout du premier onglet
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(self.view)
        self.tab_widget.addTab(tab, "Diagramme")
        
        # Barre de statut
        self.setStatusBar(self.statusBar())
        self.statusBar().showMessage("Prêt.")

    # -------------------------

    def create_menu(self):
        # --- MENU FICHIER ---
        file_menu = self.menuBar().addMenu("&Fichier")
        file_menu.setCursor(Qt.PointingHandCursor)
        # Actions
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator() 
        file_menu.addAction(self.export_action)
        file_menu.addSeparator() 
        file_menu.addAction(self.exit_action)

        # --- MENU ÉDITION ---
        edit_menu = self.menuBar().addMenu("&Édition")
        edit_menu.setCursor(Qt.PointingHandCursor) 
        # Actions
        
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        
        edit_menu.addSeparator() 
        edit_menu.addAction(self.cut_action)
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.delete_action) # Utilisation de l'action existante
        edit_menu.addSeparator()
        edit_menu.addAction(self.select_all_action)


        # Ajoutez un menu "Affichage"
        view_menu = self.menuBar().addMenu("&Affichage")
        view_menu.setCursor(Qt.PointingHandCursor)
        # Actions
        view_menu.addAction(self.show_palette_action)
        view_menu.addAction(self.show_navigationtree_action)
        view_menu.addSeparator()
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        view_menu.addSeparator()
        view_menu.addAction(self.fit_to_view_action)

        # --- NOUVEAU OUTILS ---
        tools_menu = self.menuBar().addMenu("&Outils")
        tools_menu.setCursor(Qt.PointingHandCursor) 
        # Actions
        tools_menu.addAction(self.toggle_connection_mode_action)
        tools_menu.addAction(self.toggle_grid_action)

        
        # --- MENU AIDE ---
        help_menu = self.menuBar().addMenu("&Aide")
        help_menu.setCursor(Qt.PointingHandCursor) 
        # Note: On laisse la documentation pour l'utilisateur s'il veut ajouter un lien
        help_menu.addAction(QAction("Documentation", self)) 
        help_menu.addSeparator()
        help_menu.addAction(self.about_action)
        
    # ----------------------

    def create_dock_widgets(self):
        # ... (initialisation du dock widget)

        self.tree_widget = QTreeWidget(self)
        self.tree_widget.setHeaderLabels(["Nom", "Type Ecore"])

        # AJOUTER CETTE LIGNE : Connexion du signal ITEM de l'arbre au handler
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)

        # ... (suite de l'initialisation du dock widget et ajout de self.tree_widget)
        
        # Et s'assurer que l'action du dock est connectée à la visibilité du dock (relation correcte pour QAction)
        self.show_navigationtree_action.toggled.connect(self.navigation_dock.setVisible)

    ####======================================####  

    def undo_action_handler(self):
        """Gère l'annulation de la dernière action."""
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            self.update_undo_redo_state()
            self.model_manager.save_model()  # Sauvegarder après l'annulation

    def redo_action_handler(self):
        """Gère le rétablissement de la dernière action annulée."""
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.redo()
            self.undo_stack.append(command)
            self.update_undo_redo_state()
            self.model_manager.save_model()  # Sauvegarder après le rétablissement

    def update_undo_redo_state(self):
        """Met à jour l'état des actions Undo/Redo en fonction des piles."""
        self.undo_action.setEnabled(bool(self.undo_stack))
        self.redo_action.setEnabled(bool(self.redo_stack))

    def execute_command(self, command):
        """Exécute une commande et met à jour les piles."""
        command.redo()  # Exécute la commande initialement
        if len(self.undo_stack) >= self.max_undo_limit:
            self.undo_stack.pop(0)  # Supprime la plus vieille commande si limite atteinte
        self.undo_stack.append(command)
        self.redo_stack.clear()  # Vide la pile redo lors d'une nouvelle action
        self.update_undo_redo_state()
        self.model_manager.save_model()  # Forcer la sauvegarde après chaque commande




    ####======================================####  

    def update_edit_actions_state(self):
        """
        Met à jour l'état des actions 'Couper', 'Copier' et 'Supprimer' 
        en fonction du nombre d'éléments sélectionnés.
        """
        selected_items = self.view.scene().selectedItems()
        
        # Les actions sont activées si au moins un élément est sélectionné.
        can_copy_cut_delete = bool(selected_items)
        
        # Mise à jour des boutons Couper et Copier
        self.cut_action.setEnabled(can_copy_cut_delete)
        self.copy_action.setEnabled(can_copy_cut_delete)
        
        # Assurez-vous d'avoir une action de suppression pour le test
        self.delete_action.setEnabled(can_copy_cut_delete) 

        # Note: Le bouton Coller (Paste) doit rester indépendant, 
        # car il dépend du contenu du presse-papiers, pas de la sélection actuelle.
        
    
    ####======================================####


    def set_snap_to_grid(self, enabled):
        self.snap_to_grid = enabled
        self.statusBar().showMessage(f"Accrochage à la grille: {'Activé' if enabled else 'Désactivé'}")
        
    def setup_global_connections(self):
        self.view.itemDropped.connect(self.handle_item_drop)
        #self.view.property_dropped.connect(self.handle_property_drop)

        #self.tree_widget.itemDoubleClicked.connect(self.center_view_on_item)
        
        self.tree_widget.itemDoubleClicked.connect(self.handle_tree_item_double_click)

        self.tree_widget.itemDoubleClicked.connect(self.on_tree_item_clicked)
        # Note: Le simple clic doit déjà être connecté dans le setup de l'UI :
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)

        for tool_type, button in self.tool_buttons.items():
            button.mousePressEvent = lambda event, tt=tool_type: self.start_drag(event, tt)

        self.zoom_in_action.triggered.connect(self.view.zoom_in)
        self.zoom_out_action.triggered.connect(self.view.zoom_out)
        self.fit_to_view_action.triggered.connect(self.view.fit_in_view)

        # Assurez-vous que l'exportation est également connectée ici, pour la sécurité :
        self.export_action.triggered.connect(self.export_diagram) 


    def start_drag(self, event, tool_type):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(tool_type) # Le type est la clé ici (ex: "agent", "resource")
            drag.setMimeData(mime_data)

            # Créer un pixmap pour l'icône de glisser-déposer (visuel)
            pixmap = QPixmap(100, 50)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QPen(Qt.black, 2))
            painter.setBrush(QBrush(QColor("lightblue")))
            painter.drawRect(0, 0, 99, 49)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, tool_type)
            painter.end()
            drag.setPixmap(pixmap)

            drag.setHotSpot(QPoint(50, 25))
            drag.exec(Qt.MoveAction)

    
    
    ####======================================####


    def handle_tree_item_double_click(self, item, column):
        """
        Ouvre la boîte de dialogue d'édition appropriée pour l'élément du modèle 
        sélectionné dans l'arbre de navigation.

        Réagit au double-clic sur un QTreeWidgetItem.
        Args:
            item (QTreeWidgetItem): L'élément sur lequel le double-clic a eu lieu.
            column (int): L'index de la colonne (non utilisé ici).
        """
        # Récupération des données stockées dans l'élément d'arbre
        element_type = item.data(0, Qt.UserRole)  # Ex: 'agent', 'resource', 'process', 'property'
        element_id = item.data(1, Qt.UserRole)    # ID unique de l'EObject

        # 1. Trouver l'EObject correspondant dans le modèle
        model_element = self.model_manager.get_element_by_id(element_id)
        
        # NOTE: Il est préférable d'utiliser une méthode du ModelManager pour la recherche 
        # plutôt que de parcourir tous les éléments ici. (Implémentation suggérée : 
        # self.model_manager.get_element_by_id(element_id))
        if not model_element:
             # Recherche manuelle si la méthode du ModelManager n'est pas encore disponible
            for element in self.model_manager.get_all_elements():
                if element.id == element_id:
                    model_element = element
                    break
        
        if model_element:
            dialog = None
            
            # 2. Déterminer la boîte de dialogue en fonction du type de l'élément
            if element_type == 'agent':
                # La boîte de dialogue Agent est compatible avec la classe Agent du métamodèle
                from dialogs.agentdialog import AgentDialog 
                dialog = AgentDialog(agent=model_element, parent=self)
                
            elif element_type == 'resource':
                # La boîte de dialogue Resource est compatible avec la classe Resource du métamodèle
                from dialogs.resourcedialog import ResourceDialog
                dialog = ResourceDialog(resource=model_element, parent=self)
                
            elif element_type == 'process':
                # Le type Process est abstrait, l'implémentation ProcessDialog devrait 
                # gérer les sous-classes (TransformationProcess, MovementProcess).
                # NOTE: L'argument 'current_properties' n'existe pas dans le nouveau métamodèle 
                # SocioEcosystem. Il faut le supprimer ou le remplacer si Process en a besoin.
                # ProcessDialog gère maintenant les dépendances (involvedResources, dependsOnParameters).
                from dialogs.processdialog import ProcessDialog
                
                # Ancienne ligne (à revoir selon l'implémentation de ProcessDialog)
                # dialog = ProcessDialog(process=model_element, parent=self, current_properties=self.model_manager.current_model.hasProperties)
                
                # Nouvelle approche (sans l'ancienne propriété hasProperties sur le modèle racine)
                dialog = ProcessDialog(process=model_element, parent=self) 

            elif element_type == 'property':
                # Seule la classe Parameter hérite de Property dans le nouveau métamodèle.
                # On utilise donc ParameterDialog (ou ParameterDialog) pour le type Parameter.
                
                #if isinstance(model_element, self.model_manager.Parameter):
                # NOTE: La vérification pour Variable a été retirée car elle est obsolète.
                dialog = ParameterDialog(parameter=model_element, parent=self)
                #else:
                    # Gérer les cas où le type est Property mais n'est pas une sous-classe instanciable
                #    return 

            # 3. Exécuter la boîte de dialogue et mettre à jour l'UI si acceptée
            if dialog and dialog.exec():
                # Mise à jour de l'arbre de navigation pour refléter les modifications de nom/structure.
                self.update_navigation_tree()

    ####======================================####

    def toggle_connector_menu(self):
        """
        Affiche un menu contextuel regroupant les types de connecteurs disponibles.
        Exclut les relations de containment comme holdsResources.
        """
        
        menu = QMenu(self)
        
        # --- 🔹 CONNECTEURS DISPONIBLES (UNIQUEMENT LES RÉFÉRENCES NON-CONTAINMENT) 🔹 ---
        connector_definitions = [
            # === RELATIONS AGENT (NON-CONTAINMENT) ===
            {
                "type": "containsAgents", 
                "label": "containsAgents (Agent → Agent) : Agent contient un sous-agent",
                "description": "Relation hiérarchique entre agents"
            },
            {
                "type": "isSubjectOf",
                "label": "isSubjectOf (Agent → Process) : Agent est sujet du Processus",
                "description": "L'agent initie ou exécute le processus"
            },
            {
                "type": "isObjectOf", 
                "label": "isObjectOf (Agent → Process) : Agent est objet du Processus",
                "description": "L'agent est la cible ou le bénéficiaire du processus"
            },
            
            # === RELATIONS PROCESSUS (COMMUNES) ===
            {
                "type": "involvedResources",
                "label": "involvedResources (Process → Resource) : Resource impliquée",
                "description": "Ressource utilisée ou consommée par le processus"
            },
            {
                "type": "dependsOnParameters",
                "label": "dependsOnParameters (Process → Parameter) : Dépendance paramètre", 
                "description": "Le processus dépend de la valeur de ce paramètre"
            },
            
            # === RELATIONS SPÉCIFIQUES TRANSFORMATIONPROCESS ===
            {
                "type": "affectsResources",
                "label": "affectsResources (Transformation → Resource) : Affecte Resource",
                "description": "Le processus de transformation modifie cette ressource"
            },
            
            # === RELATIONS SPÉCIFIQUES MOVEMENTPROCESS ===
            {
                "type": "source",
                "label": "source (Movement → Agent) : Source du mouvement",
                "description": "Agent source pour un processus de mouvement"
            },
            {
                "type": "destination", 
                "label": "destination (Movement → Agent) : Destination du mouvement",
                "description": "Agent destination pour un processus de mouvement"
            }
        ]

        # 1. Création des actions pour chaque type de connexion
        for connector in connector_definitions:
            action = QAction(connector["label"], self)
            action.setStatusTip(connector["description"])
            
            # Connexion avec le type de relation
            action.triggered.connect(
                lambda checked, mode=connector["type"]: self.set_connection_mode(mode)
            )
            menu.addAction(action)

        # 2. Information sur le mode actuel
        menu.addSeparator()
        if hasattr(self, 'connection_mode') and self.connection_mode:
            current_mode_action = QAction(f"Mode actuel: {self.connection_mode}", self)
            current_mode_action.setEnabled(False)
            menu.addAction(current_mode_action)
            menu.addSeparator()

        # 3. NOUVEAU : Information sur les relations automatiques
        auto_relations_action = QAction("💡 Relations automatiques : holdsResources", self)
        auto_relations_action.setStatusTip("Créé automatiquement via menu contextuel d'agent")
        auto_relations_action.setEnabled(False)
        menu.addAction(auto_relations_action)
        menu.addSeparator()

        # 4. Action pour désactiver le mode
        deactivate_action = QAction("🚫 Désactiver le mode de connexion", self)
        deactivate_action.setStatusTip("Quitter le mode de création de lien")
        deactivate_action.triggered.connect(self.deactivate_connection_mode)
        menu.addAction(deactivate_action)

        # 5. Affichage du menu à la position du curseur
        menu.exec(self.cursor().pos())

    def set_connection_mode(self, mode):
        """
        Active un mode de connexion spécifique.
        
        Args:
            mode (str): Type de relation à créer, ou None pour désactiver
        """
        
        if mode:
            self.connection_mode = mode
            self.connection_source = None
            self.connection_target = None
            
            # Message contextuel selon le type de relation
            mode_messages = {
                "containsAgents": "Sélectionnez un AGENT parent (source), puis un AGENT enfant (cible)", 
                "isSubjectOf": "Sélectionnez un AGENT (source), puis un PROCESSUS (cible)",
                "isObjectOf": "Sélectionnez un AGENT (source), puis un PROCESSUS (cible)",
                "involvedResources": "Sélectionnez un PROCESSUS (source), puis une RESSOURCE (cible)",
                "dependsOnParameters": "Sélectionnez un PROCESSUS (source), puis un PARAMÈTRE (cible)",
                "affectsResources": "Sélectionnez un PROCESSUS DE TRANSFORMATION (source), puis une RESSOURCE (cible)",
                "source": "Sélectionnez un PROCESSUS DE MOUVEMENT (source), puis un AGENT source (cible)",
                "destination": "Sélectionnez un PROCESSUS DE MOUVEMENT (source), puis un AGENT destination (cible)"
            }
            
            message = mode_messages.get(mode, f"Mode '{mode}' activé. Sélectionnez un élément source.")
            self.statusBar().showMessage(f"🔗 {message}")
            
            # Curseur spécial pour le mode connexion
            self.view.setCursor(Qt.CrossCursor)
            
        else:
            self.deactivate_connection_mode()



    ####======================================####

    def select_all_items(self):
        """Sélectionne tous les éléments QGraphicsItem dans la scène."""
        scene = self.view.scene()
        if not scene:
            return
        # Parcourt tous les éléments de la scène et les sélectionne
        for item in scene.items():
            if hasattr(item, 'model_element'): # Suppose que seuls les items du modèle doivent être sélectionnés
                item.setSelected(True)
        self.statusBar().showMessage("Tous les éléments du modèle ont été sélectionnés.", 2000)


    ####======================================####

    def toggle_grid(self):
        """Active ou désactive l'alignement sur la grille et met à jour l'affichage."""
    
        self.snap_to_grid = not self.snap_to_grid
        self.toggle_grid_action.setChecked(self.snap_to_grid)
        self.view.grid_enabled = self.snap_to_grid # Supposons que la vue a un attribut grid_enabled
        self.view.viewport().update() # Force le redessin de la vue

        status = "activé" if self.snap_to_grid else "désactivé"
        self.statusBar().showMessage(f"Alignement sur la grille {status}.", 2000)

    ####======================================####

    def show_about_dialog(self):
        """Affiche la boîte de dialogue 'À propos de...'."""
        
        # Le contenu de la boîte de dialogue
        title = "À propos de l'Éditeur Socio-Écosystème"
        
        message = (
            "<h2>Éditeur Socio-Écosystème</h2>"
            "<p>Version : 1.0.0 (MDD Editor)</p>"
            "<p>Développé pour la modélisation de systèmes complexes.</p>"
            "<p>Framework : PySide6 (Qt) et Pyecore.</p>"
            "<p>Auteur : T.S.</p>"
            "<br>"
            "Ce logiciel est une preuve de concept pour la création d'éditeurs "
            "graphiques basés sur des modèles (MDE/MDD)."
        )
        
        # Utilisation de QMessageBox pour afficher l'information
        QMessageBox.about(self, title, message)

    ####======================================####

    def toggle_connection_mode(self):
        """
        Active/désactive le mode de création de liens générique via le bouton de la toolbar.
        Permet de créer plusieurs connecteurs sans retourner à la palette.
        """
        from PySide6.QtWidgets import QMessageBox
        
        if self.connection_mode is None:
            # Activation du mode générique
            self.connection_mode = 'generic'
            self.statusBar().showMessage(
                "🔗 Mode Connexion Générique ACTIF - Sélectionnez source puis cible, "
                "puis choisissez le type de relation", 
                5000
            )
            self.view.setCursor(Qt.CrossCursor)
            if hasattr(self, 'toggle_connection_mode_action'):
                self.toggle_connection_mode_action.setChecked(True)
        else:
            # Désactivation du mode
            self.deactivate_connection_mode()

    def handle_generic_connection_selection(self, item):
        """
        Gère la sélection d'éléments en mode connexion générique.
        
        Args:
            item: Item graphique sélectionné
        """
        if self.connection_mode != 'generic':
            return
            
        if not self.connection_source:
            # Premier clic : sélection de la source
            self.connection_source = item
            item.setHighlight(True)
            self.statusBar().showMessage(
                f"Source '{item.model_element.name}' sélectionnée. Choisissez la cible."
            )
        else:
            # Second clic : sélection de la cible
            self.connection_target = item
            
            # Vérification que la source et la cible sont différentes
            if self.connection_source == self.connection_target:
                self.statusBar().showMessage("❌ Impossible de connecter un élément à lui-même", 3000)
                self.connection_source.setHighlight(False)
                self.connection_source = None
                return
                
            # Ouvre la boîte de dialogue pour choisir le type de relation
            self._select_connection_type(
                self.connection_source, 
                self.connection_target
            )

    def _select_connection_type(self, source_item, target_item):
        """
        Ouvre une boîte de dialogue pour choisir le type de lien approprié.
        
        Args:
            source_item: Item source de la connexion
            target_item: Item cible de la connexion
        """
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        
        source_element = source_item.model_element
        target_element = target_item.model_element
        source_type = source_element.eClass.name
        target_type = target_element.eClass.name
        
        # Détermination des relations possibles basée sur les types
        possible_relations = self._get_possible_relations(source_type, target_type)
        
        if not possible_relations:
            QMessageBox.information(
                self, 
                "Aucune Relation Possible",
                f"Aucune relation valide entre {source_type} et {target_type}.\n\n"
                f"Source: {source_element.name} ({source_type})\n"
                f"Cible: {target_element.name} ({target_type})"
            )
            self._reset_connection_highlight()
            return
        
        # Création de la liste des relations avec descriptions
        relation_labels = []
        for rel_type in possible_relations:
            description = self._get_relation_description(rel_type)
            relation_labels.append(f"{rel_type} : {description}")
        
        # Boîte de dialogue de sélection
        selected_label, ok = QInputDialog.getItem(
            self,
            "Choisir le Type de Relation",
            f"Relation entre {source_type} et {target_type}:\n\n"
            f"Source: {source_element.name}\n"
            f"Cible: {target_element.name}",
            relation_labels,
            0,  # Index par défaut
            False  # Non éditable
        )
        
        if ok and selected_label:
            # Extraction du type de relation depuis le label
            relation_type = selected_label.split(" : ")[0]
            
            # Validation et création de la connexion
            self._validate_and_create_connection(
                source_item, target_item, relation_type
            )
        else:
            self.statusBar().showMessage("Création de relation annulée", 2000)
            self._reset_connection_highlight()

    def _get_possible_relations(self, source_type, target_type):
        """
        Retourne les relations possibles entre deux types d'éléments.
        
        Args:
            source_type (str): Type de l'élément source
            target_type (str): Type de l'élément cible
            
        Returns:
            list: Types de relations possibles
        """
        # Mapping des relations possibles selon le métamodèle
        relation_matrix = {
            # Agent → X
            ("Agent", "Agent"): ["containsAgents"],
            ("Agent", "Process"): ["isSubjectOf", "isObjectOf"],
            ("Agent", "TransformationProcess"): ["isSubjectOf", "isObjectOf"],
            ("Agent", "MovementProcess"): ["isSubjectOf", "isObjectOf"],
            ("Agent", "Resource"): [],  # holdsResources est automatique
            
            # Process → X  
            ("Process", "Resource"): ["involvedResources"],
            ("TransformationProcess", "Resource"): ["involvedResources", "affectsResources"],
            ("MovementProcess", "Resource"): ["involvedResources"],
            ("Process", "Parameter"): ["dependsOnParameters"],
            ("TransformationProcess", "Parameter"): ["dependsOnParameters"],
            ("MovementProcess", "Parameter"): ["dependsOnParameters"],
            
            # MovementProcess → Agent (spécifique)
            ("MovementProcess", "Agent"): ["source", "destination"],
            
            # Resource → X (peu de relations sortantes)
            ("Resource", "Agent"): [],
            ("Resource", "Process"): [],
            ("Resource", "Parameter"): [],
            
            # Parameter → X (peu de relations sortantes)
            ("Parameter", "Agent"): [],
            ("Parameter", "Process"): [],
            ("Parameter", "Resource"): []
        }
        
        # Recherche des relations possibles
        direct_key = (source_type, target_type)
        if direct_key in relation_matrix:
            return relation_matrix[direct_key]
        
        # Fallback pour les sous-classes
        for (src, tgt), relations in relation_matrix.items():
            if (source_type == src or source_type.startswith(src)) and \
            (target_type == tgt or target_type.startswith(tgt)):
                return relations
        
        return []

    def _get_relation_description(self, relation_type):
        """
        Retourne la description d'un type de relation.
        
        Args:
            relation_type (str): Type de relation
            
        Returns:
            str: Description de la relation
        """
        descriptions = {
            "containsAgents": "Agent contient un sous-agent",
            "isSubjectOf": "Agent est sujet du processus", 
            "isObjectOf": "Agent est objet du processus",
            "involvedResources": "Ressource impliquée dans le processus",
            "dependsOnParameters": "Processus dépend du paramètre",
            "affectsResources": "Processus affecte la ressource",
            "source": "Agent source du mouvement",
            "destination": "Agent destination du mouvement"
        }
        return descriptions.get(relation_type, "Relation non documentée")
    '''
    def _validate_and_create_connection(self, source_item, target_item, relation_type):
        """
        Valide et crée une connexion entre deux éléments.
        
        Args:
            source_item: Item source
            target_item: Item cible  
            relation_type (str): Type de relation
        """
        from PySide6.QtWidgets import QMessageBox
        
        try:
            # Validation via ModelManager
            success, message = self.model_manager.validate_connection(
                source_item.model_element, 
                target_item.model_element, 
                relation_type
            )
            
            if success:
                # Création de la connexion
                self.create_connector_from_ui(source_item, target_item, relation_type)
                self.statusBar().showMessage(
                    f"Relation '{relation_type}' créée entre "
                    f"{source_item.model_element.name} et {target_item.model_element.name}!"
                )
            else:
                QMessageBox.warning(self, "Relation Impossible", message)
                self.statusBar().showMessage(f"❌ {message}", 5000)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création : {e}")
            self.statusBar().showMessage(f"❌ Erreur création relation", 5000)
        finally:
            # Réinitialisation dans tous les cas
            self._reset_connection_highlight()
    ''' 

    def _validate_and_create_connection(self, source_item, target_item, relation_type):
        """
        Valide et crée une connexion entre deux éléments.
        
        Args:
            source_item: Item source
            target_item: Item cible  
            relation_type (str): Type de relation
        """
        
        try:
            # Validation via ModelManager
            validation_result = self.model_manager.validate_connection( # <-- Capture le résultat dans une variable temporaire
                source_item.model_element, 
                target_item.model_element, 
                relation_type
            )
            
            # Gestion du retour None (en cas d'erreur imprévue dans le manager)
            if validation_result is None:
                success = False
                message = "Erreur interne critique: validate_connection a retourné None."
            else:
                # Décompression normale
                success, message = validation_result
            
            if success:
                # Création de la connexion
                self.create_connector_from_ui(source_item, target_item, relation_type)
                self.statusBar().showMessage(
                    f"Relation '{relation_type}' créée entre "
                    f"{source_item.model_element.name} et {target_item.model_element.name}!"
                )
            else:
                QMessageBox.warning(self, "Relation Impossible", message)
                self.statusBar().showMessage(f"❌ {message}", 5000)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création : {e}")
            self.statusBar().showMessage(f"❌ Erreur création relation", 5000)
        finally:
            # Réinitialisation dans tous les cas
            self._reset_connection_highlight()
    

    def _reset_connection_highlight(self):
        """
        Réinitialise la surbrillance et prépare pour la prochaine connexion.
        """
        if self.connection_source:
            self.connection_source.setHighlight(False)
            self.connection_source = None
        self.connection_target = None
        
        # Restauration du message pour le mode générique
        if self.connection_mode == 'generic':
            self.statusBar().showMessage(
                "🔗 Mode Connexion Générique ACTIF - Sélectionnez source puis cible", 
                5000
            )

    def update_connection_state(self, mode=None):
        """
        Gère l'activation/désactivation des modes de connexion.
        
        Args:
            mode (str): Mode spécifique ou None pour désactiver
        """        
        if mode:
            # Activation d'un mode spécifique (depuis la palette)
            self.connection_mode = mode
            self._reset_connection_highlight()
            
            mode_messages = {
                "containsAgents": "Sélectionnez un AGENT parent, puis un AGENT enfant",
                "isSubjectOf": "Sélectionnez un AGENT, puis un PROCESSUS",
                # ... autres messages spécifiques
            }
            
            message = mode_messages.get(mode, f"Mode '{mode}' activé. Sélectionnez la source.")
            self.statusBar().showMessage(f"🔗 {message}")
            self.view.setCursor(Qt.CrossCursor)
            
            # Décocher le bouton générique
            if hasattr(self, 'toggle_connection_mode_action'):
                self.toggle_connection_mode_action.setChecked(False)
                
        else:
            # Désactivation complète
            self.deactivate_connection_mode()

    def deactivate_connection_mode(self):
        """
        Désactive complètement le mode de connexion.
        """        
        self._reset_connection_highlight()
        self.connection_mode = None
        self.statusBar().showMessage("Mode de connexion désactivé")
        self.view.setCursor(Qt.ArrowCursor)
        
        # Décocher tous les boutons
        if hasattr(self, 'toggle_connection_mode_action'):
            self.toggle_connection_mode_action.setChecked(False)


    ####======================================####  

    def update_connectors_on_move(self):
        """Met à jour tous les connecteurs après le déplacement d'un item."""
        for item in self.view.scene().items():
            if isinstance(item, ConnectorItem):
                item.update_path()


    ####======================================####

    
    def setup_item_connections(self, item):
        """
        Configure les connexions de signaux (mise à jour, suppression, redimensionnement, déplacement)
        entre l'élément graphique (QGraphicsItem) et la fenêtre principale/ModelManager.
        Ces connexions permettent de synchroniser l'affichage graphique avec l'état du modèle Ecore 
        et la pile d'Undo/Redo.
        
        Args:
            item (QGraphicsItem): L'élément graphique à connecter (AgentItem, ResourceItem, etc.).
        """
        
        # NOTE: Les signaux (e.g., agent_updated, resource_deleted) sont définis dans 
        # les classes d'items graphiques respectives (agent_item.py, resource_item.py, etc.).

        if hasattr(item, 'node_updated'):
            #item.node_updated.connect(self.draw_connectors)
            item.node_updated.connect(self.update_navigation_tree)

     ####======================================####


    def serialize_selected_items(self, selected_items):
        """
        Sérialise les éléments graphiques sélectionnés en JSON, incluant le conteneur 
        dans le contexte de la sélection pour les Agents.
        """        
        if not selected_items:
            return QByteArray(b"[]") 
            
        # Créer un set des IDs des modèles sélectionnés pour une recherche rapide
        selected_model_ids = {item.model_element.id for item in selected_items if hasattr(item, 'model_element')}
        data = []
        
        for item in selected_items:
            model_element = item.model_element
            if hasattr(item, 'model_element') and isinstance(model_element, EObject):
                try:
                    node_data = {
                        'type': type(item).__name__,
                        'model': {
                            # ... (autres propriétés conservées) ...
                            'id': getattr(model_element, 'id', 'unknown_id'),
                            'name': getattr(model_element, 'name', ''),
                            'pos_x': getattr(model_element, 'pos_x', 0.0),
                            'pos_y': getattr(model_element, 'pos_y', 0.0),
                            'width': getattr(model_element, 'width', 120.0),
                            'height': getattr(model_element, 'height', 60.0),
                            'comment': getattr(model_element, 'comment', ''),
                            'description': getattr(model_element, 'description', ''), 

                            # 🔹 NOUVEAU: Enregistrer l'ancien conteneur, MAIS seulement si l'Agent conteneur est aussi dans la sélection.
                            'old_container_id': None,
                        },
                        'connectors': []
                    }
                    
                    # Logique de conteneurisation pour les agents contenus par d'autres agents
                    if model_element.eContainer() and model_element.eContainer().eClass.name == 'Agent':
                        container_id = getattr(model_element.eContainer(), 'id', None)
                        if container_id in selected_model_ids:
                             # L'élément est contenu par un autre Agent qui est aussi copié
                            node_data['model']['old_container_id'] = container_id
                            
                    # ... (Autres sérialisations de propriétés spécifiques et de relations Ecore)
                    
                    # ----------------------------------------------------
                    # Sérialisation des connecteurs (inchangée mais complète)
                    for connector in getattr(item, 'outgoing_connectors', []):
                        if connector.target in selected_items and hasattr(connector.target, 'model_element') and hasattr(connector.source, 'model_element'):
                            connector_data = {
                                'conn_type': getattr(connector, 'conn_type', 'default'),
                                'source_id': getattr(connector.source.model_element, 'id', 'unknown_source_id'),
                                'target_id': getattr(connector.target.model_element, 'id', 'unknown_target_id'),
                                'style': getattr(connector, 'style', 'solid'),
                                'control_points': [(p.x(), p.y()) for p in getattr(connector, 'control_points', [])],
                                'label': getattr(connector.label_item, 'toPlainText', lambda: '')() if getattr(connector, 'label_item', None) else ''
                            }
                            node_data['connectors'].append(connector_data)
                            
                    data.append(node_data)
                    
                except Exception as e:
                    print(f"Erreur lors de la sérialisation de {getattr(model_element, 'id', 'item inconnu')}: {e}")
                    continue
                    
        return QByteArray(json.dumps(data).encode('utf-8'))

    # Nouvelle méthode pour désérialiser et cloner
    def deserialize_and_clone(self, serialized_data, paste_position: QPointF = None):
        """
        Désérialise les données JSON, crée de nouveaux éléments et les positionne 
        autour de 'paste_position' si spécifié.
        """       
        # ... (Décodage inchangé de serialized_data en data) ...
        try:
            # Décodage QByteArray
            if isinstance(serialized_data, QByteArray):
                serialized_str = serialized_data.data().decode('utf-8')
            else:
                serialized_str = serialized_data.decode('utf-8') 
                
            if not serialized_str or serialized_str.strip() == "":
                return []
                
            data = json.loads(serialized_str)
            cloned_items = []
            id_map = {}  
            
            # Calculer le décalage (offset)
            min_x = min(node['model']['pos_x'] for node in data) if data else 0
            min_y = min(node['model']['pos_y'] for node in data) if data else 0
            
            # Utiliser la position du curseur, sinon un décalage par défaut
            if paste_position:
                offset_x = paste_position.x() - min_x 
                offset_y = paste_position.y() - min_y
            else:
                # Décalage fixe si la position du curseur n'est pas fournie (par exemple, lors d'un Redo)
                offset_x = 20
                offset_y = 20

            # 1. Création des Nœuds et gestion de la hiérarchie locale
            for node_data in data:
                cloned_model = self.model_manager.clone_element(node_data['model'])
                
                if cloned_model:
                    old_id = node_data['model']['id']
                    new_id = cloned_model.id
                    id_map[old_id] = new_id

                    # 🔹 Positionnement basé sur le décalage calculé
                    cloned_model.pos_x = node_data['model']['pos_x'] + offset_x
                    cloned_model.pos_y = node_data['model']['pos_y'] + offset_y
                    
                    # Crée l'item graphique
                    cloned_item = self.create_item_from_type(node_data['type'], cloned_model)
                    
                    if cloned_item:
                        cloned_items.append(cloned_item)
                        if hasattr(self, 'model_to_item'):
                            self.model_to_item[new_id] = cloned_item
                        
                        cloned_item.setPos(cloned_model.pos_x, cloned_model.pos_y)
                        self.scene.addItem(cloned_item)
                        
                    # 🔹 Gestion de la conteneurisation interne (Agent dans Agent)
                    old_container_id = node_data['model'].get('old_container_id')
                    if old_container_id and old_container_id in id_map:
                        new_container_id = id_map[old_container_id]
                        new_container_item = self.model_to_item.get(new_container_id)
                        
                        if new_container_item and new_container_item.model_element.eClass.name == 'Agent':
                            # Assigner l'élément cloné à la liste 'containsAgents' du conteneur cloné
                            new_container_item.model_element.containsAgents.append(cloned_model)
                            print(f"DEBUG: Agent '{cloned_model.name}' re-contenu dans Agent '{new_container_item.model_element.name}'")


            # 2. Clonage des connecteurs après les nœuds (inchangé)
            for node_data in data:
                for connector_data in node_data.get('connectors', []):
                    source_id = id_map.get(connector_data['source_id'])
                    target_id = id_map.get(connector_data['target_id'])
                    
                    if source_id and target_id:
                        source_item = self.model_to_item.get(source_id)
                        target_item = self.model_to_item.get(target_id)
                        
                        if source_item and target_item:
                            new_connector = self.create_connector_from_ui(source_item, target_item, connector_data['conn_type'])
                            
                            if new_connector:
                                new_connector.control_points = [QPointF(x, y) for x, y in connector_data['control_points']]
                                new_connector.label_item.setPlainText(connector_data['label'])
                                new_connector.update_path()
                                cloned_items.append(new_connector)

            # Post-opérations
            self.update_navigation_tree()
            self.model_manager.save_model() 
            return cloned_items
            
        # ... (Gestion des exceptions inchangée) ...
        except json.JSONDecodeError as e:
            print(f"Erreur JSON lors du clonage : {e}")
            return []
        except Exception as e:
            print(f"Erreur lors du clonage : {e}")
            return []

    # Nouvelle méthode pour créer un item par type
    def create_item_from_type(self, item_type, model_element):
        """
        Crée un item graphique à partir de son type et d'un élément modèle Ecore.
        
        Mise à jour pour: Suppression de la classe obsolète 'VariableItem'.
        
        Args:
            item_type (str): Nom de la classe de l'item (ex. 'AgentItem', 'ResourceItem').
            model_element: Élément modèle Ecore correspondant à l'item.
            
        Returns:
            QGraphicsItem: L'item créé, ou None si le type n'est pas pris en charge.
        """
        # NOTE: Les imports des classes d'items sont supposés se trouver en tête de main.py
        try:
            if item_type == 'AgentItem':
                # Assurez-vous d'avoir l'import: from items.agent_item import AgentItem
                return AgentItem(model_element, self)
            elif item_type == 'ResourceItem':
                # Assurez-vous d'avoir l'import: from items.resource_item import ResourceItem
                return ResourceItem(model_element, self)
            elif item_type == 'ProcessItem':
                # Assurez-vous d'avoir l'import: from items.process_item import ProcessItem
                return ProcessItem(model_element, self)
            # 🔹 Suppression de VariableItem, remplacé par l'unique ParameterItem pour Property.
            # elif item_type == 'VariableItem': 
            #     return VariableItem(model_element, self)
            elif item_type == 'ParameterItem':
                # Assurez-vous d'avoir l'import: from items.parameter_item import ParameterItem
                return ParameterItem(model_element, self)
            else:
                print(f"Type d'item non pris en charge : {item_type}")
                return None
        except Exception as e:
            print(f"Erreur lors de la création de l'item {item_type} : {e}")
            return None

    # Implémentation des méthodes
    def copy_selected_items(self):
        """
        Copie les éléments sélectionnés dans le presse-papiers sous le format MIME personnalisé.
        """

        selected_items = self.view.scene().selectedItems()
        # Ne considérer que les éléments qui peuvent être sérialisés (Agent, Resource, Process, Parameter)
        serializable_items = [
            item for item in selected_items 
            if hasattr(item, 'model_element') 
            and item.model_element.eClass.name in ['Agent', 'Resource', 'TransformationProcess', 'MovementProcess', 'Parameter']
        ]

        if not serializable_items:
            self.statusBar().showMessage("Aucun élément sérialisable sélectionné.", 2000)
            return
            
        # Utilise la méthode refactorisée qui inclut la gestion des conteneurs
        serialized_data = self.serialize_selected_items(serializable_items)
        
        mime_data = QMimeData()
        # 🔹 Utiliser le format MIME défini
        mime_data.setData(self.clipboard_data_format, serialized_data) 
        
        self.clipboard.setMimeData(mime_data)
        # 🔹 Mettre à jour l'état de l'action Coller
        self.update_paste_action_state() 
        self.statusBar().showMessage(f"{len(serializable_items)} éléments copiés.")

    def cut_selected_items(self):
        """
        Coupe les éléments sélectionnés (copie dans le presse-papiers puis supprime via une commande Undo/Redo).
        """
        selected_items = self.view.scene().selectedItems()
        if not selected_items:
            return
            
        # 1. Copier dans le presse-papiers
        self.copy_selected_items()
        
        # 2. Exécuter la commande de suppression (gère la désélection et l'Undo/Redo)
        # Note: DeleteItemsCommand doit pouvoir gérer les connecteurs et les nœuds
        self.execute_command(DeleteItemsCommand(self, selected_items)) 
        self.statusBar().showMessage(f"{len(selected_items)} éléments coupés.")

    def paste_items(self):
        """
        Colle les éléments du presse-papiers en utilisant la position du curseur comme point de référence.
        """
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if not mime_data.hasFormat(self.clipboard_data_format):
            self.statusBar().showMessage("Rien de valide à coller.", 2000)
            return
            
        serialized_data = mime_data.data(self.clipboard_data_format)
        
        # 🔹 NOUVEAU: Détermination de la position de collage dans la scène
        cursor_pos_global = QCursor.pos() 
        # Convertit la position globale en position dans la vue
        cursor_pos_view = self.view.mapFromGlobal(cursor_pos_global)
        # Convertit la position de la vue en position dans la scène (coordonnées du modèle)
        paste_pos_scene = self.view.mapToScene(cursor_pos_view)
        
        # 🔹 Appel de deserialize_and_clone avec la position de collage
        # La méthode refactorisée dans la section précédente utilise ce second argument.
        cloned_items = self.deserialize_and_clone(serialized_data, paste_pos_scene)
        
        if cloned_items:
            # Enregistrer la commande pour l'Undo/Redo
            self.execute_command(PasteItemsCommand(self, cloned_items))

            # UX: Sélectionner les nouveaux éléments
            self.view.scene().clearSelection()
            for item in cloned_items:
                if isinstance(item, QGraphicsItem):
                    item.setSelected(True)
            
            self.statusBar().showMessage(f"{len(cloned_items)} éléments collés.")
        else:
            self.statusBar().showMessage("Le collage a échoué ou les données étaient invalides.", 2000)

    def update_paste_action_state(self):
        """
        Met à jour l'état de l'action Coller en fonction du contenu du presse-papiers.
        """
        if not hasattr(self, 'clipboard_data_format'):
             # Utile pour l'initialisation de MainWindow
            self.clipboard_data_format = 'application/x-socioecosystem-elements' 
            
        try:
            can_paste = QApplication.clipboard().mimeData().hasFormat(self.clipboard_data_format)
            self.paste_action.setEnabled(can_paste)
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'état Coller : {e}")
            self.paste_action.setEnabled(False)
    

    ####======================================####

    def create_agent_item(self, pos):
        """
        Crée un nouvel agent à la position spécifiée.
        
        Args:
            pos (QPointF): Position où créer l'agent
        """
        if not self.model_manager.current_model:
            self.statusBar().showMessage("Veuillez créer ou ouvrir un modèle avant d'ajouter des éléments.")
            QMessageBox.warning(self, "Erreur", "Veuillez créer ou ouvrir un modèle avant d'ajouter des éléments.")
            return
        
        # Application de la grille si activée
        if self.snap_to_grid:
            pos.setX(round(pos.x() / self.grid_size) * self.grid_size)
            pos.setY(round(pos.y() / self.grid_size) * self.grid_size)
            
        # Ouvre la boîte de dialogue de création d'agent
        dialog = AgentDialog(
            agent=None,
            parent=self,
            existing_ids=[agent.id for agent in self.model_manager.current_model.agents],
            main_window=self
        )
        
        if dialog.exec():
            data = dialog.get_data()
            
            # Créer l'agent sans l'ajouter au modèle immédiatement
            agent = self.model_manager.create_agent(data, add_to_model=True)
            if not agent:
                return

            # Configuration des propriétés graphiques
            agent.pos_x = pos.x()
            agent.pos_y = pos.y()
            agent.width = AgentItem.DEFAULT_WIDTH
            agent.height = AgentItem.DEFAULT_HEIGHT
            
            # Création de l'item graphique
            item = AgentItem(agent, self)
            item.setPos(pos)
            self.setup_item_connections(item)
            
            # Ajout via le système de commandes (undo/redo)
            self.execute_command(AddNodeCommand(self, item, agent))
            
            # Mise à jour de l'interface et sauvegarde
            self.update_navigation_tree()
            self.view.itemAdded.emit()
            self.statusBar().showMessage(f"Agent '{data['name']}' ajouté.")
            

    def create_contained_resource(self, parent_agent_item):
        """
        Crée une ressource contenue par un agent (via menu contextuel).
        """

        if not self.model_manager.current_model:
            QMessageBox.warning(self, "Erreur", "Modèle non chargé.")
            return

        parent_agent_model = parent_agent_item.model_element
        
        # Position par défaut (décalée à l'intérieur de l'agent pour une bonne UX)
        pos = parent_agent_item.pos() + QPointF(20, 20) 
        
        # CORRECTION : Préparer les données pour ResourceDialog
        # Toutes les ressources existantes (pour validation IDs)
        existing_resources = [
            prop for prop in self.model_manager.current_model.properties 
            if hasattr(prop, 'eClass') and prop.eClass.name == 'Resource'
        ]
        existing_ids = [resource.id for resource in existing_resources]
        
        # Tous les agents disponibles
        current_agents = self.model_manager.current_model.agents

        # APPEL CORRECT avec les bons paramètres
        dialog = ResourceDialog(
            resource=None,  # Nouvelle ressource
            parent=self,
            existing_ids=existing_ids,
            current_agents=current_agents,  # Tous les agents
            connected_entities={
                'heldBy': parent_agent_model  # Déjà liée à l'agent parent
            }
        )
        
        if dialog.exec():
            data = dialog.get_data()
            
            # Création de la ressource via ModelManager
            resource = self.model_manager.create_resource(data, add_to_model=True)
            if not resource:
                return
                    
            # Établissement de la relation holdsResources
            resource.heldBy = parent_agent_model  # ✅ Essential pour l'introspection

            #if resource not in self.model_manager.current_model.properties:
            #    self.model_manager.current_model.properties.append(resource)

            if resource not in parent_agent_model.holdsResources:
                parent_agent_model.holdsResources.append(resource)
            
            # Configuration des propriétés graphiques
            resource.pos_x = pos.x()
            resource.pos_y = pos.y()
            resource.width = ResourceItem.DEFAULT_WIDTH
            resource.height = ResourceItem.DEFAULT_HEIGHT
            
            # Création de l'item graphique
            item = ResourceItem(resource, self)
                        
            item.setPos(pos)
            self.setup_item_connections(item)

            # CRÉATION AUTOMATIQUE DU CONNECTEUR holdsResources
            self._create_holdsResources_connector(parent_agent_item, item)

            # Ajout via le système de commandes
            self.execute_command(AddNodeCommand(self, item, resource))
            
            # Mise à jour de l'interface
            self.update_navigation_tree()
            self.view.itemAdded.emit()
            self.statusBar().showMessage(
                f"Ressource '{data['name']}' ajoutée à l'agent '{parent_agent_model.name}'."
            )

    def _create_holdsResources_connector(self, agent_item, resource_item):
        """
        Crée automatiquement le connecteur holdsResources entre un agent et une ressource.
        
        Args:
            agent_item: Item graphique de l'agent
            resource_item: Item graphique de la ressource
        """
        from items.connector_item import ConnectorItem
        
        conn_type = "holdsResources"
        source_id = agent_item.model_element.id
        target_id = resource_item.model_element.id
        key = (source_id, target_id, conn_type)

        # Style du connecteur pour holdsResources
        connection_style = self._get_connector_style(conn_type).copy()
        connection_style['type'] = 'straight'  # Connecteur droit par défaut
        
        # Création du connecteur graphique
        connector = ConnectorItem(
            agent_item, 
            resource_item, 
            conn_type, 
            connection_style, 
            [],  # Pas de points de contrôle
            self
        )

        # Ajout à la scène
        self.scene.addItem(connector)
        
        # Mise à jour des références dans les items
        agent_item.outgoing_connectors.append(connector)
        resource_item.incoming_connectors.append(connector)

        # Connexion des signaux
        self.setup_connector_connections(connector)

        # SAUVEGARDE des métadonnées pour la sérialisation
        self.model_manager.connector_types[key] = 'straight'
        # Pas de label par défaut pour les relations automatiques


    def create_process_item(self, pos):
        """
        Crée un nouveau processus à la position spécifiée.
        
        Args:
            pos (QPointF): Position où créer le processus
        """
        
        if not self.model_manager.current_model:
            self.statusBar().showMessage("Veuillez créer ou ouvrir un modèle avant d'ajouter des éléments.")
            QMessageBox.warning(self, "Erreur", "Veuillez créer ou ouvrir un modèle avant d'ajouter des éléments.")
            return
            
        if self.snap_to_grid:
            pos.setX(round(pos.x() / self.grid_size) * self.grid_size)
            pos.setY(round(pos.y() / self.grid_size) * self.grid_size)
            
        # Ouvre la boîte de dialogue ProcessDialog
        dialog = ProcessDialog(
            parent=self,
            existing_ids=[process.id for process in self.model_manager.current_model.processes],
            # Récupération de toutes les ressources disponibles pour les relations
            current_resources=[resource for agent in self.model_manager.current_model.agents 
                             for resource in agent.holdsResources]
        )
        
        if dialog.exec():
            data = dialog.get_data()

            #print(f"🔍 DEBUG PROCESS - Données reçues: {data.keys()}")
            #print(f"🔍 DEBUG PROCESS - Type: {data.get('process_type')}")
            
            # Création du processus via ModelManager
            process = self.model_manager.create_process(data, add_to_model=True)
            if not process:
                return
            
            # Configuration des propriétés graphiques
            process.pos_x = pos.x()
            process.pos_y = pos.y()
            process.width = ProcessItem.DEFAULT_WIDTH
            process.height = ProcessItem.DEFAULT_HEIGHT
            
            # Création de l'item graphique
            item = ProcessItem(process, self)
            self.scene.addItem(item)
            item.setPos(pos)
            self.setup_item_connections(item)
            self.model_to_item[process.id] = item

            # Ajout via le système de commandes
            self.execute_command(AddNodeCommand(self, item, process))
            
            # Mise à jour de l'interface et sauvegarde
            self.update_navigation_tree()
            self.view.itemAdded.emit()
            self.statusBar().showMessage(f"Processus '{data['name']}' ajouté.")

    def create_parameter_item(self, pos):
        """
        Crée un nouveau paramètre à la position spécifiée.
        
        Args:
            pos (QPointF): Position où créer le paramètre
        """
        
        if not self.model_manager.current_model:
            self.statusBar().showMessage("Veuillez créer ou ouvrir un modèle avant d'ajouter des éléments.")
            QMessageBox.warning(self, "Erreur", "Veuillez créer ou ouvrir un modèle avant d'ajouter des éléments.")
            return
            
        if self.snap_to_grid:
            pos.setX(round(pos.x() / self.grid_size) * self.grid_size)
            pos.setY(round(pos.y() / self.grid_size) * self.grid_size)
            
        # Ouvre la boîte de dialogue ParameterDialog
        dialog = ParameterDialog(
            parent=self,
            existing_ids=[param.id for param in self.model_manager.current_model.properties 
                         if hasattr(param, 'eClass') and param.eClass.name == 'Parameter']
        )
        
        if dialog.exec():
            data = dialog.get_data()
            
            # Création du paramètre via ModelManager
            parameter = self.model_manager.create_parameter(data, add_to_model=True)
            if not parameter:
                return
            
            # Configuration des propriétés graphiques
            parameter.pos_x = pos.x()
            parameter.pos_y = pos.y()
            parameter.width = ParameterItem.DEFAULT_WIDTH
            parameter.height = ParameterItem.DEFAULT_HEIGHT
            
            # Création de l'item graphique
            item = ParameterItem(parameter, self)
            self.scene.addItem(item)
            item.setPos(pos)
            self.setup_item_connections(item)
            self.model_to_item[parameter.id] = item

            # Ajout via le système de commandes
            self.execute_command(AddNodeCommand(self, item, parameter))
            
            # Mise à jour de l'interface et sauvegarde
            self.update_navigation_tree()
            self.view.itemAdded.emit()
            self.statusBar().showMessage(f"Paramètre '{data['name']}' ajouté.")

    def handle_item_drop(self, item_type, scene_pos):
        """
        Gère l'événement de glisser-déposer depuis la palette vers la scène.
        
        Args:
            item_type (str): Type d'élément à créer
            scene_pos (QPointF): Position sur la scène
        """
        
        if not isinstance(item_type, str):
            self.statusBar().showMessage(f"Erreur : Type d'élément invalide ({item_type}).", 5000)
            return
            
        item_type = item_type.lower()
        
        # Dictionnaire des méthodes de création supportées
        create_methods = {
            "agent": self.create_agent_item,
            "process": self.create_process_item,
            "property": self.create_parameter_item
        }
        
        # Vérification spécifique pour les ressources
        if item_type == "resource":
            self.statusBar().showMessage(
                "Utilisez le menu contextuel d'un agent (clic droit → '➕ Ajouter une Ressource')", 
                7000
            )
            QMessageBox.information(
                self, 
                "Création de ressource", 
                "Pour créer une ressource :\n\n1. Faites un clic droit sur un agent\n"
                "2. Sélectionnez '➕ Ajouter une Ressource'\n\n"
                "Cette ressource sera automatiquement liée à l'agent."
            )
            return

        # Exécution de la méthode de création
        create_method = create_methods.get(item_type)
        
        if create_method:
            create_method(scene_pos)
        else:
            self.statusBar().showMessage(f"Type d'élément non supporté : {item_type}", 5000)
    

    ####======================================####

        
    def create_connector_from_ui(self, source_item, target_item, conn_type):
        """
        Crée le connecteur graphique et le lien Ecore correspondant.
        Utilise AddConnectorCommand pour l'Undo/Redo.
        
        Args:
            source_item: Item graphique source
            target_item: Item graphique cible  
            conn_type (str): Type de connexion selon le métamodèle
        """
       
        if not source_item or not target_item:
            self.statusBar().showMessage("Erreur : Source ou cible de la connexion manquante.", 5000)
            return
            
        # 1. Validation et création du lien Ecore via ModelManager
        success, message = self.model_manager.create_connector_link(
            source_item.model_element, target_item.model_element, conn_type
        )

        if not success:
            QMessageBox.warning(self, "Erreur de connexion", message)
            self.statusBar().showMessage(f"Échec de la connexion : {message}", 5000)
            return

        # 2. Création de l'élément graphique (ConnectorItem)
        source_id = source_item.model_element.id 
        target_id = target_item.model_element.id
        key = (source_id, target_id, conn_type)

        # Style du connecteur basé sur le type de relation
        connection_style = self._get_connector_style(conn_type)
        
        # Récupération des métadonnées de sérialisation
        connector_type = self.model_manager.connector_types.get(key, 'straight')
        control_points = self.model_manager.control_points.get(key, [])
        
        # Application du type au style
        connection_style['type'] = connector_type
        
        # Création de l'objet graphique
        connector = ConnectorItem(
            source_item, 
            target_item, 
            conn_type, 
            connection_style, 
            control_points, 
            self
        )

        # Ajout à la scène et connexions
        self.scene.addItem(connector)
        source_item.outgoing_connectors.append(connector)
        target_item.incoming_connectors.append(connector)

        # Connexion des signaux
        connector.connector_label_updated_signal.connect(self.handle_connector_label_update)
        connector.control_points_updated_signal.connect(self.handle_control_point_update)
        connector.connector_deleted_signal.connect(self.handle_connector_deletion)
        connector.connector_type_updated_signal.connect(self.handle_connector_type_update)

        # Mise à jour des métadonnées pour la sérialisation
        self.model_manager.connector_types[key] = connector_type
        
        # 3. Enregistrement de la commande pour Undo/Redo
        self.execute_command(AddConnectorCommand(
            self, connector, source_item.model_element, 
            target_item.model_element, conn_type
        ))

        # Feedback utilisateur et sauvegarde
        self.statusBar().showMessage(
            f"Connexion '{conn_type}' créée entre {source_item.model_element.name} et {target_item.model_element.name}."
        )
        self.update_navigation_tree()
        self.model_manager.save_model()

    def _get_connector_style(self, conn_type):

        """
        Détermine le style visuel d'un connecteur selon son type.
        
        Args:
            conn_type (str): Type de connexion
            
        Returns:
            dict: Configuration de style avec label
        """
        # Styles par défaut pour les différents types de relations
        style_configs = {
            # === RELATIONS AGENT ===
            "holdsResources": {
                "color": "#2E86AB", 
                "style": Qt.SolidLine, 
                "width": 2,
                "label": "détient",  
                "description": "Agent détient une Resource"
            },
            "containsAgents": {
                "color": "#A23B72", 
                "style": Qt.DashLine, 
                "width": 2,
                "label": "contient",  
                "description": "Agent contient un sous-agent"
            },
            "isSubjectOf": {
                "color": "#F18F01", 
                "style": Qt.SolidLine, 
                "width": 2,
                "label": "sujet de",  
                "description": "Agent est sujet du Processus"
            },
            "isObjectOf": {
                "color": "#C73E1D", 
                "style": Qt.SolidLine, 
                "width": 2,
                "label": "objet de",  
                "description": "Agent est objet du Processus"
            },
            
            # === RELATIONS PROCESSUS ===
            "involvedResources": {
                "color": "#3BB273", 
                "style": Qt.SolidLine, 
                "width": 2,
                "label": "implique",  
                "description": "Processus implique une Resource"
            },
            "dependsOnParameters": {
                "color": "#7768AE", 
                "style": Qt.DotLine, 
                "width": 2,
                "label": "dépend de",  
                "description": "Processus dépend d'un Paramètre"
            },
            
            # === RELATIONS SPÉCIFIQUES TRANSFORMATIONPROCESS ===
            "affectsResources": {
                "color": "#E15554", 
                "style": Qt.SolidLine, 
                "width": 3,
                "label": "affecte",  
                "description": "TransformationProcess affecte une Resource"
            },
            
            # === RELATIONS SPÉCIFIQUES MOVEMENTPROCESS ===
            "source": {
                "color": "#4D9DE0", 
                "style": Qt.SolidLine, 
                "width": 2, 
                "arrow": "source",
                "label": "source",  
                "description": "Agent source du MovementProcess"
            },
            "destination": {
                "color": "#E1BC29", 
                "style": Qt.SolidLine, 
                "width": 2, 
                "arrow": "destination",
                "label": "destination",  
                "description": "Agent destination du MovementProcess"
            }
        }
        
        # Style par défaut pour les relations non reconnues
        default_style = {
            "color": "#000000", 
            "style": Qt.SolidLine, 
            "width": 1,
            "label": conn_type,  
            "description": f"Relation {conn_type}"
        }
        
        return style_configs.get(conn_type, default_style).copy()

    def handle_connector_deletion(self, source_model, target_model, conn_type):
        """
        Gère la suppression d'un connecteur dans le modèle.
        
        Args:
            source_model: Élément modèle source
            target_model: Élément modèle cible
            conn_type (str): Type de connexion
        """
        
        success, message = self.model_manager.delete_connector_link(source_model, target_model, conn_type)
        
        if success:
            self.statusBar().showMessage(message)
            self.update_navigation_tree()
            self.model_manager.save_model()
        else:
            QMessageBox.warning(self, "Erreur de suppression", message)
            self.statusBar().showMessage(f"Échec de suppression : {message}", 5000)

    def handle_connector_label_update(self, source_id, target_id, conn_type, new_label):
        """
        Gère la mise à jour du label d'un connecteur.
        
        Args:
            source_id (str): ID de l'élément source
            target_id (str): ID de l'élément cible
            conn_type (str): Type de connexion
            new_label (str): Nouveau label
        """
        self.model_manager.update_connector_label(source_id, target_id, conn_type, new_label)
        self.statusBar().showMessage(f"Label '{conn_type}' mis à jour : {new_label}")

    def handle_control_point_update(self, source_id, target_id, conn_type, control_points):
        """
        Gère la mise à jour des points de contrôle d'un connecteur.
        
        Args:
            source_id (str): ID de l'élément source
            target_id (str): ID de l'élément cible  
            conn_type (str): Type de connexion
            control_points (list): Nouveaux points de contrôle
        """
        self.model_manager.update_control_points(source_id, target_id, conn_type, control_points)
        self.statusBar().showMessage(f"Points de contrôle '{conn_type}' mis à jour")

    def handle_connector_type_update(self, source_id, target_id, conn_type, connector_type):
        """
        Gère la mise à jour du type de connecteur (droit/courbe/orthogonal).
        
        Args:
            source_id (str): ID de l'élément source
            target_id (str): ID de l'élément cible
            conn_type (str): Type de connexion
            connector_type (str): Type de tracé ('straight', 'curved', 'orthogonal')
        """
        key = (source_id, target_id, conn_type)
        self.model_manager.connector_types[key] = connector_type
        self.model_manager.save_model()
        self.statusBar().showMessage(f"Type de connecteur '{conn_type}' changé en {connector_type}")
    
    
    ####======================================####

    def prepare_and_delete_selected_items(self):
        """
        Point d'entrée pour la suppression déclenchée par l'Action (Menu/Raccourci).
        Récupère les items sélectionnés et appelle la méthode de suppression centrale.
        """
        selected_items = self.view.scene().selectedItems()
        if selected_items:
            # Appel de la méthode centrale (déjà nommée delete_selected_items)
            self.delete_selected_items(selected_items)

    def keyPressEvent(self, event):
        """
        Gère les raccourcis clavier. Déclenche l'action 'Delete' si la touche est pressée.
        """
        # 💡 Qt gère normalement cela, mais pour forcer l'utilisation de l'Action:
        if event.key() == Qt.Key_Delete and self.delete_action.isEnabled():
            self.delete_action.trigger() # Déclenche l'action, qui appelle prepare_and_delete_selected_items
            return # Consomme l'événement
            
        super().keyPressEvent(event)

    def delete_selected_items(self, items_to_delete: list):
        """
        Gère la suppression des éléments sélectionnés (nœuds et connecteurs)
        en assurant la suppression Ecore, l'invalidation des liens et l'Undo/Redo.
        """        
        
        if not items_to_delete:
            return

        # 1. Préparation des listes
        nodes_to_delete = [item for item in items_to_delete if hasattr(item, 'model_element')]
        connectors_to_delete = [item for item in items_to_delete if isinstance(item, ConnectorItem)]
        
        all_elements_to_delete = []

        # 2. Gestion des Nœuds
        # La suppression d'un nœud implique la suppression de tous ses connecteurs associés.
        for node in nodes_to_delete:
            # Ajouter le nœud à la liste principale de suppression
            all_elements_to_delete.append(node)
            
            # Ajouter les connecteurs du nœud à la liste des connecteurs à supprimer
            # (sans doublon et uniquement si pas déjà dans la liste principale)
            for connector in node.outgoing_connectors + node.incoming_connectors:
                if connector not in connectors_to_delete:
                    connectors_to_delete.append(connector)

        # 3. Gestion des Connecteurs (ceux initialement sélectionnés ou liés aux nœuds)
        for connector in connectors_to_delete:
            if connector not in all_elements_to_delete:
                all_elements_to_delete.append(connector)

        # 4. Exécution de la commande de suppression
        
        # 4.1 Supprimer les Connecteurs (doit être fait avant les nœuds pour invalider les liens Ecore)
        for connector in connectors_to_delete:
            source = connector.source.model_element
            target = connector.target.model_element
            conn_type = connector.conn_type

            # Exécuter la commande de suppression du lien Ecore et du graphique
            # NOTE: La commande doit gérer la suppression de l'élément de la collection/relation Ecore
            command = DeleteConnectorCommand(self, connector, source, target, conn_type)
            self.execute_command(command)
        
        # 4.2 Supprimer les Nœuds
        # Nous utilisons une commande pour chaque nœud pour simplifier le Undo/Redo
        for node in nodes_to_delete:
            # NOTE: La commande doit gérer la suppression de l'élément de son conteneur Ecore
            command = DeleteNodeCommand(self, node, node.model_element)
            self.execute_command(command)
            
        # 5. Mise à jour de l'interface
        self.update_navigation_tree()
        self.model_manager.save_model()
        self.view.scene().update()

    ####======================================####

    def update_navigation_tree(self):
        """
        Met à jour l'arbre de navigation en utilisant la structure de confinement et de référence Ecore.
        """
        icons_path = Path(__file__).parent / "icons"
        self.tree_widget.clear()

        model = self.model_manager.current_model
        if not model:
            return

        # 1. Créer le nœud racine du Modèle
        model_root = QTreeWidgetItem([f"🌍 Modèle: {getattr(model, 'name', 'Non nommé')}", model.eClass.name])
        self.tree_widget.addTopLevelItem(model_root)

        # 2. Lancer le peuplement récursif à partir du Modèle (SocioEcosystem)
        self._populate_tree(model, model_root, icons_path)

        # 3. Finalisation
        model_root.setExpanded(True)
        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)
        def center_view_on_item(self, item, column):
            item_text = item.text(0)
            item_type = item.text(1)
            
            target_model = None
            if item_type == "Agent":
                target_model = next((a for a in self.model_manager.current_model.agents if a.name == item_text), None)
            elif item_type == "Resource":
                target_model = next((r for r in self.model_manager.current_model.resources if r.name == item_text), None)
            elif item_type == "Process":
                target_model = next((p for p in self.model_manager.current_model.hasProcesses if p.name == item_text), None)
            elif item_type in ["Parameter", "Variable"]:
                target_model = next((p for p in self.model_manager.current_model.hasProperties if p.name == item_text), None)

            if target_model and target_model in self.model_to_item:
                target_item = self.model_to_item[target_model]
                self.view.centerOn(target_item)
    
    # Dans main.py (méthode de MainWindow)

    def _populate_tree(self, parent_ecore_element: EObject, parent_tree_item: QTreeWidgetItem, icons_path: Path):
        """
        Parcourt récursivement les relations de confinement et de référence d'un élément Ecore
        pour construire les branches de l'arbre.
        """
        
        features = parent_ecore_element.eClass.eAllStructuralFeatures()

        # --- 1. TRAITEMENT DES RELATIONS DE CONFINEMENT (Hiérarchie d'éléments) ---
        for feature in features:
            if isinstance(feature, EReference):
                if feature.containment and feature.many:
                    # Récupérer la collection (ex: model.agents ou agent.containsAgents)
                    collection = parent_ecore_element.eGet(feature)
                    if not collection:
                        continue

                    feature_name = feature.name
                    metadata = ITEM_METADATA.get(feature_name)
                    
                    # Créer le nœud intermédiaire pour la collection (ex: 👥 Agents)
                    collection_label = metadata["label"] if metadata else f"Conteneur: {feature_name}"
                    collection_root = QTreeWidgetItem([collection_label])
                    
                    # Utiliser l'icône de la collection si définie dans le mapping de la feature
                    if metadata and metadata.get("icon"):
                        collection_root.setIcon(0, QIcon(str(icons_path / metadata["icon"])))
                    
                    parent_tree_item.addChild(collection_root)

                    # Récursion: Parcourir les éléments contenus
                    for element in collection:
                        self._add_ecore_element_to_tree_item(element, collection_root, icons_path)

            # Nous ignorons les relations de confinement 1..1 pour ne pas surcharger l'arbre,
            # elles sont souvent gérées comme des propriétés de l'élément parent.


    # --- 2. TRAITEMENT DES RELATIONS DE RÉFÉRENCE (Liens non-contenants) ---
        # Nous parcourons toutes les autres relations EReference pour afficher les liens
        for feature in features:
            if isinstance(feature, EReference) and not feature.containment:
                
                feature_name = feature.name
                
                # Récupérer les éléments référencés (que ce soit 1..1 ou 1..*)
                referenced_elements = parent_ecore_element.eGet(feature)
                
                # Convertir en liste si c'est une relation 1..1 non nulle, ou utiliser la collection
                if not feature.many and referenced_elements:
                    referenced_elements = [referenced_elements]
                elif not feature.many and not referenced_elements:
                    continue # Relation 1..1 nulle
                elif feature.many and not referenced_elements:
                    continue # Collection 1..* vide

                # Créer un nœud intermédiaire pour la catégorie de référence (ex: Ressources Déténues)
                feature_metadata = ITEM_METADATA.get(feature_name, {})
                category_label = feature_metadata.get('label_prefix', f"Références: {feature_name}")
                category_item = QTreeWidgetItem([category_label])
                
                # Optionnel: définir l'icône de la catégorie si le lien a une icône dédiée
                if feature_metadata.get("icon"):
                    category_item.setIcon(0, QIcon(str(icons_path / feature_metadata["icon"])))
                    
                parent_tree_item.addChild(category_item)
                
                # Parcourir les éléments référencés
                for referenced_element in referenced_elements:
                    self._add_ecore_reference_item(referenced_element, category_item, icons_path, feature_name)



    def _add_ecore_element_to_tree_item(self, ecore_element: EObject, parent_tree_item: QTreeWidgetItem, icons_path: Path):
        """
        Crée un QTreeWidgetItem pour un élément Ecore CONTENU et lance la récursion.
        """
        element_type_name = ecore_element.eClass.name
        metadata = ITEM_METADATA.get(element_type_name, {})
        
        # Libellé: (Préfixe de l'élément + Nom de l'élément)
        name = getattr(ecore_element, 'name', element_type_name)
        item_label = f"{metadata.get('label_prefix', '')}{name}"
        
        element_child = QTreeWidgetItem([item_label, element_type_name])
        
        # Icône et Data
        if metadata.get("icon"):
            element_child.setIcon(0, QIcon(str(icons_path / metadata["icon"])))
        element_child.setData(0, Qt.UserRole, ecore_element)
        
        parent_tree_item.addChild(element_child)
        
        # Poursuivre la récursion à partir de l'élément nouvellement ajouté
        self._populate_tree(ecore_element, element_child, icons_path)


    def _add_ecore_reference_item(self, ecore_element: EObject, parent_tree_item: QTreeWidgetItem, icons_path: Path, feature_name: str):
        """
        Crée un QTreeWidgetItem pour un élément Ecore RÉFÉRENCÉ (pas de récursion).
        Le préfixe est déjà géré par le parent category_item.
        """
        element_type_name = ecore_element.eClass.name
        metadata_element = ITEM_METADATA.get(element_type_name, {})
        metadata_feature = ITEM_METADATA.get(feature_name, {})
        
        # Libellé: (Préfixe de la Feature + Nom de l'élément référencé)
        name = getattr(ecore_element, 'name', element_type_name)
        item_label = f"{metadata_feature.get('label_prefix', '')}{name}"
        
        element_child = QTreeWidgetItem([item_label, element_type_name])
        
        # Icône et Data
        # Utiliser l'icône de l'élément référencé (Resource, Agent, Parameter)
        if metadata_element.get("icon"):
            element_child.setIcon(0, QIcon(str(icons_path / metadata_element["icon"])))
        element_child.setData(0, Qt.UserRole, ecore_element)
        
        parent_tree_item.addChild(element_child)


    def on_tree_item_clicked(self, item, column):
        """
        Gère le clic sur un élément dans l'arbre de navigation.
        Récupère l'objet Ecore et centre la vue sur l'élément graphique correspondant.
        """
        # Récupérer l'objet Ecore stocké dans le rôle utilisateur de la première colonne
        model_element = item.data(0, Qt.UserRole)

        if model_element is None:
            # L'élément cliqué est un conteneur racine (ex: "Agents") et n'a pas d'objet Ecore associé
            return

        if not isinstance(model_element, EObject):
            # Sécurité : l'objet récupéré doit être un élément Ecore
            return

        # 1. Sélection et Centrage dans la scène graphique
        
        # 1.1. Désélectionner tous les éléments de la scène pour une sélection propre
        self.view.scene().clearSelection()
        
        # 1.2. Rechercher l'élément graphique (NodeItem) correspondant à l'objet Ecore
        # La liste 'model_to_item' fait le lien entre l'objet Ecore et l'objet graphique
        if model_element in self.model_to_item:
            graphics_item = self.model_to_item[model_element]
            
            # Sélectionner l'élément graphique
            graphics_item.setSelected(True)
            
            # Centrer la vue sur l'élément sélectionné
            # Utiliser la méthode centerOn de QGraphicsView (self.view)
            self.view.centerOn(graphics_item.pos()) 
            
        else:
            # L'élément Ecore existe (ex: Resource détenue) mais peut ne pas avoir d'élément graphique
            # s'il s'agit d'un élément contenu (comme un Paramètre ou une Resource imbriquée dans un Agent,
            # dans un design où seuls les Agents sont des nœuds graphiques de haut niveau).
            # Dans ce cas, nous passons directement à la mise à jour des propriétés.
            pass

        # 2. Affichage des propriétés dans le panneau de détails
        # (Supposons que vous ayez une méthode pour cela)
        self.update_property_panel(model_element)


    # Note: Assurez-vous d'avoir une structure self.model_to_item = {} dans MainWindow
    # pour mapper les instances Ecore (Resource, Agent, Parameter...) à leurs QGraphicsItem correspondants.

    def update_property_panel(self, model_element: EObject):
        """
        Met à jour le panneau d'édition des propriétés pour l'élément Ecore donné.
        (Ceci est un sketch de la fonction, l'implémentation UI réelle dépend de vos widgets)
        """
        
        # Effacer l'ancien contenu du panneau (self.property_layout est un QVBoxLayout)
        if not hasattr(self, 'property_panel_frame'):
            # Initialiser une structure de panneau de propriétés si elle n'existe pas
            return
            
        # Nettoyage
        for i in reversed(range(self.property_layout.count())): 
            widget = self.property_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
                
        # Ajouter un titre
        title = QLabel(f"Détails: {model_element.eClass.name} - {getattr(model_element, 'name', 'Non nommé')}")
        title.setProperty("class", "H2") # Style CSS si utilisé
        self.property_layout.addWidget(title)
        self.property_layout.addWidget(QFrame(frameShape=QFrame.HLine))


        # Parcourir les attributs et références de l'élément Ecore
        for feature in model_element.eClass.eAllStructuralFeatures():
            if feature.name in ['id', 'partOf', 'partOfParentAgent', 'pos_x', 'pos_y', 'width', 'height']:
                # Ignorer les métadonnées techniques ou les relations inverses
                continue

            feature_name = feature.name
            value = model_element.eGet(feature)
            
            label = QLabel(f"{feature_name}:")
            self.property_layout.addWidget(label)
            
            # Si c'est un EAttribute (Propriété simple comme name, description, quantity)
            if isinstance(feature, EAttribute):
                editor = QLineEdit(str(value) if value is not None else "")
                
                # TODO: Connecter le signal d'édition à la méthode model_manager.update_attribute
                
                self.property_layout.addWidget(editor)
            
            # Si c'est une EReference (Relation vers un autre objet)
            elif isinstance(feature, EReference):
                # Afficher le nombre d'éléments pour les collections
                if feature.many:
                    count = len(value) if value else 0
                    ref_label = QLabel(f"Références ({count} éléments)")
                    self.property_layout.addWidget(ref_label)
                else:
                    # Afficher le nom de l'objet référencé
                    name = getattr(value, 'name', 'None')
                    ref_label = QLabel(f"Cible: {name}")
                    self.property_layout.addWidget(ref_label)
            

        self.property_layout.addStretch(1)


    ####===========================================####


    # Nouvelle méthode pour gérer la suppression du connecteur
    def delete_connector_graphic_and_model(self, source_model, target_model, style):
        """
        Supprime le connecteur du modèle et de la scène graphique.
        Slot connecté au signal de ConnectorItem.
        """
        self.model_manager.delete_connector_link(source_model, target_model, style)
        self.update_navigation_tree()
        self.statusBar().showMessage("Connecteur supprimé.")


    def new_model(self):
        if self.model_manager.current_model and not self.ask_for_save():
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Nouveau modèle", "", "XMI Files (*.xmi)")
        if filename:
            self.model_manager.new_model(filename)
            self.statusBar().showMessage("Nouveau modèle créé.")
            self.scene.clear()
            self.model_to_item.clear()
            self.update_navigation_tree()
        

    def open_model(self):
        if self.model_manager.current_model and not self.ask_for_save():
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Ouvrir un modèle Ecore", "", "Fichiers Ecore (*.xmi)")
        if filename:
            self.model_manager.open_model(filename)
            self.statusBar().showMessage(f"Modèle '{filename}' ouvert.")
            self.scene.clear()
            self.model_to_item.clear()
            self.draw_model()
            self.update_navigation_tree()

    def save_model(self):
        if not self.model_manager.current_model:
            QMessageBox.warning(self, "Erreur", "Aucun modèle à sauvegarder.")
            return

        if self.model_manager.current_file:
            self.model_manager.save_model()
            self.statusBar().showMessage(f"Modèle sauvegardé dans '{self.model_manager.current_file}'.")
        else:
            self.save_as_model()

            
    def save_as_model(self):
        if not self.model_manager.current_model:
            QMessageBox.warning(self, "Erreur", "Aucun modèle à sauvegarder.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le modèle sous...", "", "Fichiers Ecore (*.xmi)")
        if file_path:
            self.model_manager.current_file = file_path
            self.model_manager.save_model(file_path)
            self.statusBar().showMessage(f"Modèle sauvegardé dans '{file_path}'.")

    def ask_for_save(self):
        if self.model_manager.current_model:
            reply = QMessageBox.question(self, "Enregistrer le modèle",
                                         "Voulez-vous enregistrer le modèle actuel avant de continuer?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if reply == QMessageBox.Save:
                self.save_model()
                return True
            elif reply == QMessageBox.Discard:
                return True
            else:
                return False
        return True


    ####======================================####


    def draw_model(self):
        """
        Dessine l'ensemble du modèle Ecore chargé et rétablit les connexions.
        Structure optimisée, deux passes : nœuds d'abord, puis connecteurs.
        """
        if not self.model_manager.current_model:
            print("Aucun modèle courant à dessiner.")
            return

        # 1. Nettoyage
        self.scene.clear()
        self.model_to_item = {}
        element_to_item_map = {}

        # --- PASS 1 : DESSINER TOUS LES NŒUDS ---
        print("PASS 1 : Dessin des nœuds (propriétés, processus, agents)")

        # 1. Propriétés (Resources, Parameters)
        for prop in self.model_manager.current_model.properties:
            item_class = None
            if hasattr(prop, 'eClass'):
                if prop.eClass.name == "Resource":
                    item_class = ResourceItem
                elif prop.eClass.name == "Parameter":
                    item_class = ParameterItem
            if item_class:
                self._draw_node(prop, item_class, element_to_item_map)

        # 2. Processus
        for process in self.model_manager.current_model.processes:
            self._draw_node(process, ProcessItem, element_to_item_map)

        # 3. Agents (récursif ou plat — ici plat, mais contient containsAgents)
        for agent in self.model_manager.current_model.agents:
            self._draw_node(agent, AgentItem, element_to_item_map)

        # --- PASS 2 : RECRÉER TOUS LES CONNECTEURS ---
        print("PASS 2 : Reconstruction des connecteurs")

        # Relations à ignorer (containment ou techniques)
        excluded_relations = {
            'partOf',           # opposite de agents
            'heldBy',           # opposite de holdsResources
            'partOfParentAgent',# opposite de containsAgents
            'subjects',         # opposite de isSubjectOf
            'objects',          # opposite de isObjectOf
        }

        # Relations à DESSINER comme connecteurs
        drawable_relations = {
            'containsAgents',     # Hiérarchie entre agents
            'holdsResources',     # Agent détient Resource
            'isSubjectOf',        # Agent → Process
            'isObjectOf',         # Agent → Process
            'involvedResources',  # Process → Resource
            'affectsResources',   # TransformationProcess → Resource
            'dependsOnParameters',# Process → Parameter
            'source',             # MovementProcess → Agent
            'destination',        # MovementProcess → Agent
        }

        # Parcourir tous les éléments dessinés
        for source_id, source_item in element_to_item_map.items():
            source_model = source_item.model_element

            for feature in source_model.eClass.eAllReferences():
                conn_type = feature.name

                # Ignorer les relations non graphiques ou containment (sauf containsAgents)
                if feature.containment and conn_type != 'containsAgents':
                    continue
                if conn_type in excluded_relations:
                    continue
                if conn_type not in drawable_relations:
                    continue

                targets = self._get_relation_targets(source_model, feature)
                for target_model in targets:
                    if not target_model:
                        continue

                    target_item = element_to_item_map.get(target_model.id)
                    if not target_item:
                        print(f"AVERTISSEMENT: Cible non trouvée pour {conn_type}: {target_model.id}")
                        continue

                    # Créer le connecteur
                    self._create_connector_from_serialized_data(
                        source_item, target_item, conn_type,
                        source_model.id, target_model.id
                    )

        # Mise à jour finale
        self.update_navigation_tree()
        self.view.viewport().update()
        print("Modèle dessiné avec succès.")

   
    def _get_relation_targets(self, source_model, feature):
        """
        Récupère les cibles d'une relation, gère les références simples et multiples.
        
        Args:
            source_model: Élément source
            feature: Feature de référence Ecore
            
        Returns:
            list: Liste des cibles
        """
        targets = source_model.eGet(feature)
        
        if not feature.many:
            # Référence simple (ex: source, destination)
            return [targets] if targets else []
        else:
            # Référence multiple (ex: containsAgents, involvedResources)
            # S'assure de retourner une liste (EList) même si None est retourné
            return list(targets) if targets is not None else []
        

    def _create_connector_from_serialized_data(self, source_item, target_item, conn_type, source_id, target_id):
        """
        Crée un connecteur à partir des données sérialisées.
        
        Args:
            source_item: Item source
            target_item: Item cible
            conn_type (str): Type de connexion
            source_id (str): ID de l'élément source
            target_id (str): ID de l'élément cible
        """
        from items.connector_item import ConnectorItem
        
        # Clé pour retrouver les métadonnées sérialisées
        key = (source_id, target_id, conn_type)
        
        # Récupération du style selon le type de relation
        connection_style = self._get_connector_style(conn_type) #.copy()

        # Récupérer le label par défaut du style
        default_label = connection_style.get('label', '')
        
        # Application des métadonnées sérialisées
        connection_style.update({
            # Utiliser default_label comme valeur de repli
            'label': self.model_manager.connector_labels.get(key, default_label), 
            'type': self.model_manager.connector_types.get(key, 'straight')
        })
        
        # Récupération des points de contrôle sérialisés
        control_points = self.model_manager.control_points.get(key, [])
        
        # Création du connecteur graphique
        connector = ConnectorItem(
            source_item, 
            target_item, 
            conn_type, 
            connection_style, 
            control_points, 
            self
        )
        
        # Ajout à la scène
        self.scene.addItem(connector)
        
        # Mise à jour des références dans les items
        source_item.outgoing_connectors.append(connector)
        target_item.incoming_connectors.append(connector)
        
        # Connexion des signaux
        self.setup_connector_connections(connector)

    def _draw_node(self, model_element, ItemClass, element_to_item_map):
        """
        Dessine un nœud générique et gère les connexions de signaux.
        
        Args:
            model_element: Élément modèle à dessiner
            ItemClass: Classe de l'item graphique
            element_to_item_map: Carte des éléments dessinés
            
        Returns:
            L'item graphique créé
        """
        # Vérification des attributs de position
        pos_x = getattr(model_element, 'pos_x', 0.0)
        pos_y = getattr(model_element, 'pos_y', 0.0)
        
        # Valeurs par défaut pour les dimensions si absentes
        width = getattr(model_element, 'width', 120.0)
        height = getattr(model_element, 'height', 60.0)
        
        # Création de l'item graphique
        item = ItemClass(model_element, self)
        item.setPos(pos_x, pos_y)
        
        # Application des dimensions si l'item les supporte
        if hasattr(item, 'setSize'):
            item.setSize(width, height)
        
        self.scene.addItem(item)
        
        # Mise à jour des cartes de référence
        element_to_item_map[model_element.id] = item
        self.model_to_item[model_element.id] = item
        
        # Connexion des signaux de l'élément
        self.setup_item_connections(item)
        
        return item

    def setup_item_connections(self, item):
        """
        Connecte les signaux d'un item graphique à la MainWindow.
        
        Args:
            item: Item graphique à connecter
        """
        # Connexion des signaux communs à tous les items
        if hasattr(item, 'item_selected_signal'):
            item.item_selected_signal.connect(self.handle_item_selection)
        
        if hasattr(item, 'item_moved_signal'):
            item.item_moved_signal.connect(self.handle_item_movement)
        
        if hasattr(item, 'item_double_clicked_signal'):
            item.item_double_clicked_signal.connect(self.handle_item_double_click)
        
        # Connexions spécifiques aux agents
        if hasattr(item, 'agent_context_menu_requested'):
            item.agent_context_menu_requested.connect(self.handle_agent_context_menu)

    def setup_connector_connections(self, connector):
        """
        Connecte les signaux d'un connecteur à la MainWindow.
        
        Args:
            connector: Connecteur à connecter
        """
        connector.connector_deleted_signal.connect(self.handle_connector_deletion)
        connector.connector_label_updated_signal.connect(self.handle_connector_label_update)
        connector.control_points_updated_signal.connect(self.handle_control_point_update)
        connector.connector_type_updated_signal.connect(self.handle_connector_type_update)
        
        # Installation des filtres d'événements si nécessaire
        if hasattr(connector, 'install_event_filters'):
            connector.install_event_filters()


    ####======================================####


    class ExportDialog(QDialog):
        def __init__(self, parent=None, scene_rect=None):
            super().__init__(parent)
            self.setWindowTitle("Options d'exportation")
            self.scene_rect = scene_rect or QRectF()
            layout = QVBoxLayout()

            # Groupbox pour PDF
            pdf_group = QGroupBox("Options PDF")
            pdf_layout = QVBoxLayout()

            # Format papier
            self.paper_format = QComboBox()
            self.paper_format.addItems(["A4", "A3", "Letter", "Legal"])
            pdf_layout.addWidget(QLabel("Format papier :"))
            pdf_layout.addWidget(self.paper_format)

            # Orientation
            self.orientation = QComboBox()
            self.orientation.addItems(["Portrait", "Paysage"])
            self.orientation.setCurrentText("Paysage")  # AJOUT : Paysage par défaut
            pdf_layout.addWidget(QLabel("Orientation :"))
            pdf_layout.addWidget(self.orientation)

            # Marges
            self.margin_mm = QSpinBox()
            self.margin_mm.setRange(0, 50)
            self.margin_mm.setValue(10)
            self.margin_mm.setSingleStep(5)
            pdf_layout.addWidget(QLabel("Marges (mm) :"))
            pdf_layout.addWidget(self.margin_mm)

            # Résolution DPI
            self.dpi = QSpinBox()
            self.dpi.setRange(72, 1200)
            self.dpi.setValue(300)
            self.dpi.setSingleStep(10)
            pdf_layout.addWidget(QLabel("Résolution DPI :"))
            pdf_layout.addWidget(self.dpi)

            pdf_group.setLayout(pdf_layout)
            layout.addWidget(pdf_group)

            # Qualité JPEG
            self.jpeg_quality = QSpinBox()
            self.jpeg_quality.setRange(0, 100)
            self.jpeg_quality.setValue(90)
            layout.addWidget(QLabel("Qualité JPEG (0-100) :"))
            layout.addWidget(self.jpeg_quality)

            # Fond transparent
            self.transparent_bg = QCheckBox("Fond transparent (PNG)")
            self.transparent_bg.setChecked(True)
            layout.addWidget(self.transparent_bg)

            # Inclure la grille
            self.include_grid = QCheckBox("Inclure la grille")
            self.include_grid.setChecked(False)
            layout.addWidget(self.include_grid)

            # Boutons
            buttons = QHBoxLayout()
            ok_button = QPushButton("Exporter")
            cancel_button = QPushButton("Annuler")
            ok_button.clicked.connect(self.accept)
            cancel_button.clicked.connect(self.reject)
            buttons.addWidget(ok_button)
            buttons.addWidget(cancel_button)
            layout.addLayout(buttons)

            self.setLayout(layout)

        def get_options(self):
            return {
                "paper_format": self.paper_format.currentText(),
                "orientation": self.orientation.currentText(),
                "margin_mm": self.margin_mm.value(),
                "dpi": self.dpi.value(),
                "jpeg_quality": self.jpeg_quality.value(),
                "transparent_bg": self.transparent_bg.isChecked(),
                "include_grid": self.include_grid.isChecked()
            }

    def add_grid_to_scene(self, scene, rect, grid_size):
        """Ajoute une grille temporaire à la scène avec des QGraphicsLineItem en arrière-plan."""
        grid_items = []
        pen = QPen(QColor(200, 200, 200), 1)
        pen.setStyle(Qt.DotLine)

        # Lignes verticales
        left = int(rect.left())
        x = left - (left % grid_size)
        while x < rect.right():
            line = QGraphicsLineItem(x, rect.top(), x, rect.bottom())
            line.setPen(pen)
            line.setZValue(-1000)
            scene.addItem(line)
            grid_items.append(line)
            x += grid_size

        # Lignes horizontales
        top = int(rect.top())
        y = top - (top % grid_size)
        while y < rect.bottom():
            line = QGraphicsLineItem(rect.left(), y, rect.right(), y)
            line.setPen(pen)
            line.setZValue(-1000)
            scene.addItem(line)
            grid_items.append(line)
            y += grid_size

        print(f"DEBUG: Grille ajoutée à la scène : {len(grid_items)} lignes, z-value=-1000")
        return grid_items

    def export_diagram(self):
        """Exporter le diagramme en PNG, JPEG, SVG ou PDF avec rendu robuste et grille."""
        filter_str = (
            "Images PNG (*.png);;"
            "Images JPEG (*.jpeg *.jpg);;"
            "Images SVG (*.svg)"
        )
        """
        # inclus le pdf quand ça va marche
        filter_str = (
            "Images PNG (*.png);;"
            "Images JPEG (*.jpeg *.jpg);;"
            "Images SVG (*.svg);;"
            "Fichiers PDF (*.pdf)"
        )
        """
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exporter le diagramme",
            "diagramme_socioecosysteme.png",
            filter_str
        )
        if not file_path:
            return

        scene = self.view.scene()
        if not scene or not scene.items():
            QMessageBox.warning(self, "Exportation annulée", "La scène est vide.")
            return

        # Calcul de la zone du diagramme
        margin_scene = 50.0
        source_rect = scene.itemsBoundingRect().adjusted(-margin_scene, -margin_scene, margin_scene, margin_scene)
        if source_rect.isNull():
            QMessageBox.critical(self, "Erreur", "Impossible de calculer la zone du diagramme.")
            return

        # Boîte de dialogue pour options
        dialog = self.ExportDialog(self, source_rect)
        if not dialog.exec():
            return
        options = dialog.get_options()

        # Sauvegarder l'état de la grille dans la vue
        original_grid_enabled = self.view.grid_enabled
        grid_items = []

        # Log des z-values des items existants pour débogage
        print("DEBUG: z-values des items avant ajout de la grille:", [(type(item).__name__, item.zValue()) for item in scene.items()])

        try:
            # Ajouter la grille à la scène si nécessaire
            if options["include_grid"]:
                grid_items = self.add_grid_to_scene(scene, source_rect, self.grid_size)

            # --- Export PDF ---
            if file_path.lower().endswith(".pdf"):
                success = self.export_diagram_pdf(file_path, options)
                if success:
                    self.statusBar().showMessage(f"PDF exporté : {file_path}", 5000)
                return


            # --- Export SVG ---
            if file_path.lower().endswith(".svg"):
                generator = QSvgGenerator()
                generator.setFileName(file_path)
                generator.setViewBox(source_rect)  # mapping scene -> svg
                generator.setTitle("Diagramme socio-écosystème")
                generator.setDescription("Export généré par l’éditeur graphique")

                painter = QPainter(generator)
                painter.setRenderHint(QPainter.Antialiasing)
                scene.render(painter, target=source_rect, source=source_rect, aspectRatioMode=Qt.KeepAspectRatio)
                painter.end()

                self.statusBar().showMessage(f"Diagramme exporté en SVG : {file_path}", 5000)
                return


            # --- Export PNG/JPEG ---
            scale_factor = options["dpi"] / 72.0
            image_size = QSizeF(source_rect.size().width() * scale_factor, source_rect.size().height() * scale_factor).toSize()
            min_width, min_height = 1920, 1080
            image_size.setWidth(max(image_size.width(), min_width))
            image_size.setHeight(max(image_size.height(), min_height))

            image = QImage(image_size, QImage.Format_ARGB32)
            image.fill(Qt.transparent if options["transparent_bg"] else Qt.white)

            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            try:
                painter.setFont(QFontDatabase().font("Arial", "Regular", 10))
                #QPainter.setFont(QFont("Arial", 10))
            except Exception as e:
                print(f"Erreur lors du chargement de la police Arial : {e}")
                painter.setFont(self.font())

            target_rect = QRectF(0, 0, image.width(), image.height())
            scene.render(painter, target=target_rect, source=source_rect, aspectRatioMode=Qt.KeepAspectRatio)
            painter.end()

            if file_path.lower().endswith(('.jpg', '.jpeg')):
                white_bg = QImage(image.size(), QImage.Format_RGB32)
                white_bg.fill(Qt.white)
                p = QPainter(white_bg)
                p.drawImage(0, 0, image)
                p.end()
                image = white_bg

            save_options = {}
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                save_options["quality"] = options["jpeg_quality"]

            if image.save(file_path, **save_options):
                self.statusBar().showMessage(f"Diagramme exporté : {file_path}", 5000)
            else:
                QMessageBox.critical(self, "Erreur", f"Impossible d’exporter vers : {file_path}")

        finally:
            # Supprimer la grille temporaire de la scène
            for item in grid_items:
                scene.removeItem(item)
            print(f"DEBUG: Supprimé {len(grid_items)} lignes de grille")
            # Restaurer l'état de la grille dans la vue
            self.view.grid_enabled = original_grid_enabled
            self.view.viewport().update()

    import pymupdf  # AJOUT : Import de PyMuPDF pour post-traitement

    def scene_to_pixmap(scene, background_color=Qt.white, scale_factor=4.0):
        """
        Convertit une QGraphicsScene en QImage haute résolution.
        Compatible pour export PDF et images.
        """
        if scene is None:
            raise ValueError("La scène fournie est None.")

        rect = scene.itemsBoundingRect()
        if rect.isNull():
            rect = QRectF(0, 0, 100, 100)

        image = QImage(
            int(rect.width() * scale_factor),
            int(rect.height() * scale_factor),
            QImage.Format_ARGB32
        )
        image.fill(background_color)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(scale_factor, scale_factor)
        scene.render(painter, target=QRectF(image.rect()), source=rect)
        painter.end()

        return image


    def export_diagram_pdf(self, file_path: str, options: dict):
        """
        Exporte la scène du diagramme en PDF :
        - centrage automatique fiable
        - mise à l’échelle correcte
        - compatibilité PyMuPDF / PySide6
        """
        try:
            from items.connector_item import ConnectorHandle
        except Exception:
            ConnectorHandle = None

        scene = self.view.scene()
        if not scene or not scene.items():
            QMessageBox.warning(self, "Export annulé", "La scène est vide.")
            return False

        original_grid_enabled = self.view.grid_enabled
        grid_items = []

        try:
            # Déterminer la zone utile de la scène
            total_bounding_rect = scene.itemsBoundingRect()
            raw = [(it, it.sceneBoundingRect()) for it in scene.items()
                if it.isVisible() and it.sceneBoundingRect().isValid()]

            candidates = [
                (it, br) for it, br in raw
                if not (ConnectorHandle and isinstance(it, ConnectorHandle))
                and br.width() > 1 and br.height() > 1
                and abs(br.x()) < 10000 and abs(br.y()) < 10000
            ]

            source_rect = total_bounding_rect if not candidates else QRectF()
            if candidates:
                for _, br in candidates:
                    source_rect = source_rect.united(br) if not source_rect.isNull() else br
                source_rect = source_rect.adjusted(-20, -20, 20, 20)

            if source_rect.isNull():
                QMessageBox.critical(self, "Erreur", "Impossible de déterminer la zone du diagramme.")
                return False

            # Ajouter la grille si demandé
            if options.get("include_grid", False):
                grid_items = self.add_grid_to_scene(scene, source_rect, self.grid_size)

            # Configuration de l’imprimante PDF
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setResolution(options.get("dpi", 300))
            paper_format = {"A4": QPageSize.A4, "A3": QPageSize.A3,
                            "Letter": QPageSize.Letter, "Legal": QPageSize.Legal}[options["paper_format"]]
            orientation = QPageLayout.Orientation.Landscape if options["orientation"] == "Paysage" else QPageLayout.Orientation.Portrait
            margins = QMarginsF(options["margin_mm"], options["margin_mm"], options["margin_mm"], options["margin_mm"])
            printer.setPageLayout(QPageLayout(QPageSize(paper_format), orientation, margins))

            # Détermination des dimensions de la page et du facteur d’échelle
            page_rect = QRectF(printer.pageRect(QPrinter.Point))
            dpi_factor = options["dpi"] / 72.0
            source_width = source_rect.width()
            source_height = source_rect.height()

            margin_points = options["margin_mm"] * 72.0 / 25.4
            scale = min(
                (page_rect.width() - 2 * margin_points) / (source_width * dpi_factor),
                (page_rect.height() - 2 * margin_points) / (source_height * dpi_factor)
            )
            scale = max(scale, 0.5)

            target_width = source_width * dpi_factor * scale
            target_height = source_height * dpi_factor * scale
            target_x = (page_rect.width() - target_width) / 2
            target_y = (page_rect.height() - target_height) / 2
            target_rect = QRectF(target_x, target_y, target_width, target_height)

            # Rendu dans le PDF
            painter = QPainter()
            if not painter.begin(printer):
                QMessageBox.critical(self, "Erreur", "Impossible d'initialiser QPainter pour le PDF.")
                return False

            painter.setRenderHint(QPainter.Antialiasing)
            #painter.setFont(QFont("Arial", 10))

            # 🔹 Ne pas translater la scène — on se base uniquement sur target_rect
            scene.render(painter, target=target_rect, source=source_rect, aspectRatioMode=Qt.KeepAspectRatio)
            painter.end()

            # Post-traitement PyMuPDF pour recentrer proprement
            import fitz
            doc = fitz.open(file_path)
            for page in doc:
                media_box = page.rect
                offset_x = (media_box.width - target_width) / 2
                offset_y = (media_box.height - target_height) / 2
                matrix = fitz.Matrix(1, 0, 0, 1, offset_x, offset_y)
                if hasattr(page, "apply_transform"):
                    page.apply_transform(matrix)
                elif hasattr(page, "set_transformation_matrix"):
                    page.set_transformation_matrix(matrix)
            doc.saveIncr()
            doc.close()

            print("DEBUG: Export PDF terminé et centré correctement.")
            return True

        finally:
            for item in grid_items:
                scene.removeItem(item)
            self.view.grid_enabled = original_grid_enabled
            self.view.viewport().update()
        
 
    ####======================================####


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Passez l'instance 'app' à MainWindow
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec())