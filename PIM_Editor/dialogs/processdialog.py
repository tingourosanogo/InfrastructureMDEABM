"""
Dialog for editing or creating Process elements.
Handles different process types with flexible connectivity and visual warnings.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QTextEdit, QMessageBox, QLabel,
    QListWidget, QAbstractItemView, QListWidgetItem, QHBoxLayout, QPushButton,
    QGroupBox, QStackedWidget, QWidget, QGridLayout
)
from PySide6.QtCore import Qt
from pyecore.ecore import EObject

import sys
from pathlib import Path

# Configure path for root modules
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from commands import ModifyFieldCommand


class ProcessDialog(QDialog):
    """
    Dialog for editing or creating Process elements.
    
    This dialog provides flexible connectivity with visual warnings for
    missing required references, rather than blocking validation.
    """

    # Mapping for TransformationType enumeration
    TRANSFORMATION_TYPE_MAPPING = {
        "Production": "Production",
        "Consommation": "Consumption", 
        "Modification": "Modification",
        "Dégradation": "Degradation",
        "Auto-transformation": "AutoTransformation"
    }

    def __init__(
        self, 
        process: EObject = None, 
        parent=None, 
        existing_ids=None, 
        current_agents=None,
        current_resources=None,
        current_parameters=None,
        connected_entities=None
    ):
        """
        Initialize the ProcessDialog.
        
        Args:
            process: Existing process object to edit, or None for creation
            parent: Parent widget
            existing_ids: List of existing process IDs for uniqueness validation
            current_agents: List of available agents for subject/object references
            current_resources: List of available resources
            current_parameters: List of available parameters
            connected_entities: Dictionary of pre-connected entities
        """
        super().__init__(parent)
        
        self.process = process
        self.old_values = {}
        self.existing_ids = existing_ids or []
        self.current_agents = current_agents or []
        self.current_resources = current_resources or []
        self.current_parameters = current_parameters or []
        self.connected_entities = connected_entities or {
            'subjects': None,
            'object': [],
            'involvedResources': [],
            'dependsOnParameters': [],
            'affectsResources': [],
            'source': None,
            'destination': None
        }
        
        self._determine_process_type()
        self._setup_dialog_configuration()
        self._init_ui()
        self._load_data()
        self._save_initial_values()
        self._update_visual_warnings()

    def _determine_process_type(self):
        """Determine the process type based on the existing process or default."""
        if self.process:
            self.process_type = self.process.eClass.name
        else:
            self.process_type = "Process"

    def _setup_dialog_configuration(self):
        """Configure basic dialog settings."""
        title_suffix = {
            "Process": "Processus",
            "TransformationProcess": "Processus de Transformation", 
            "MovementProcess": "Processus de Mouvement"
        }
        title = title_suffix.get(self.process_type, "Processus")
        
        self.setWindowTitle(f"Éditer {title}" if self.process else f"Nouveau {title}")
        self.resize(500, 650)

    def _init_ui(self):
        """Initialize the main user interface with a two-column layout."""
        # Le layout principal reste QVBoxLayout pour contenir le QGridLayout et les boutons/labels
        main_layout = QVBoxLayout(self)
        self.setMinimumWidth(850) # Assurer une largeur suffisante pour deux colonnes

        self._add_info_label(main_layout)
        
        # 1. Création du conteneur en grille pour les groupes principaux
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        
        # 2. Création et ajout des groupes à la grille
        
        # A. Type de Processus (Ligne 0, Colonne 0, span 2 colonnes)
        type_group = self._setup_process_type_selector_group()
        # Nous allons le placer au-dessus de la grille, ou le faire étirer sur 2 colonnes.
        # Pour une meilleure visibilité, laissons-le dans le main_layout mais en le modifiant.
        # (Nous utilisons une méthode pour ne pas alourdir _init_ui)
        main_layout.addWidget(type_group)

        # B. Informations de base (Ligne 1, Colonne 0 - Gauche, le plus long)
        form_group = self._setup_form_group_content()
        grid_layout.addWidget(form_group, 0, 0, 2, 1) # Ligne 0, Colonne 0, span 2 lignes

        # C. Attributs spécifiques (Ligne 0, Colonne 1 - Droite, haut)
        specific_group = self._setup_process_specific_group_content()
        grid_layout.addWidget(specific_group, 0, 1)

        # D. Références (Ligne 1, Colonne 1 - Droite, bas)
        references_group = self._setup_references_group_content()
        grid_layout.addWidget(references_group, 1, 1)

        # 3. Ajout du conteneur de grille au layout principal
        main_layout.addWidget(grid_container)
        
        # 4. Sections restantes (Warnings et boutons)
        self._setup_visual_warnings_section(main_layout)
        
        # Ajouter un étirement avant les warnings pour que la grille ne colle pas les boutons
        main_layout.addStretch(1) 
        
        self._setup_button_box(main_layout)
        
        # Nous n'avons plus besoin des appels individuels ici :
        # self._add_info_label(main_layout) # Déplacé
        # self._setup_process_type_selector(main_layout) # Déplacé
        # self._setup_form_group(main_layout) # Remplacé
        # self._setup_process_specific_group(main_layout) # Remplacé
        # self._setup_references_group(main_layout) # Remplacé
        # self._setup_visual_warnings_section(main_layout) # Déplacé
        # self._setup_button_box(main_layout) # Déplacé

    # --- NOUVELLES MÉTHODES POUR CONSERVER LA CLARTÉ ---

    def _setup_process_type_selector_group(self):
        """Factorisation de _setup_process_type_selector pour un retour de groupe."""
        type_group = QGroupBox("Type de Processus")
        type_layout = QHBoxLayout(type_group)
        
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Processus de Transformation", "Processus de Mouvement"])
        
        self.type_mapping = {
            "Processus de Transformation": "TransformationProcess", 
            "Processus de Mouvement": "MovementProcess"
        }
        
        current_display_name = next(
            (k for k, v in self.type_mapping.items() if v == self.process_type), 
            "Processus"
        )
        self.type_combo.setCurrentText(current_display_name)
        self.type_combo.setEnabled(self.process is None)
        
        if self.process is None:
            self.type_combo.currentTextChanged.connect(self._on_process_type_changed)
            
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        # Remplacement de l'ajout au main_layout par le retour du groupe
        # main_layout.addWidget(type_group) 
        return type_group

    def _setup_form_group_content(self):
        """Factorisation de _setup_form_group pour un retour de groupe."""
        form_group = QGroupBox("Informations de base")
        form_layout = QFormLayout(form_group)
        
        self._setup_id_field(form_layout)
        self._setup_name_field(form_layout)
        self._setup_equation_field(form_layout)
        self._setup_pseudocode_field(form_layout)
        self._setup_description_field(form_layout)
        self._setup_comment_field(form_layout)
        
        # Remplacement de l'ajout au main_layout par le retour du groupe
        # main_layout.addWidget(form_group)
        return form_group

    def _setup_process_specific_group_content(self):
        """Factorisation de _setup_process_specific_group pour un retour de groupe."""
        self.specific_group = QGroupBox("Attributs spécifiques au type de processus")
        self.specific_layout = QVBoxLayout(self.specific_group)
        
        self.stacked_widget = QStackedWidget()
        
        # Base Process
        base_widget = QWidget()
        base_layout = QVBoxLayout(base_widget)
        base_label = QLabel("Processus de base - pas d'attributs spécifiques supplémentaires.")
        base_label.setStyleSheet("color: gray; font-style: italic;")
        base_layout.addWidget(base_label)
        self.stacked_widget.addWidget(base_widget)
        
        # Transformation Process
        transformation_widget = QWidget()
        transformation_layout = QFormLayout(transformation_widget)
        self._setup_transformation_specific(transformation_layout)
        self.stacked_widget.addWidget(transformation_widget)
        
        # Movement Process  
        movement_widget = QWidget()
        movement_layout = QFormLayout(movement_widget)
        self._setup_movement_specific(movement_layout)
        self.stacked_widget.addWidget(movement_widget)
        
        self.specific_layout.addWidget(self.stacked_widget)
        
        self._update_specific_ui()
        
        # Remplacement de l'ajout au main_layout par le retour du groupe
        # main_layout.addWidget(self.specific_group)
        return self.specific_group

    def _setup_references_group_content(self):
        """Factorisation de _setup_references_group pour un retour de groupe."""
        references_group = QGroupBox("Références (Gérées par Connexions Graphiques)")
        references_layout = QVBoxLayout(references_group)
        
        # Subject display (DOIT être un QLineEdit car unique)
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Sujet (Agent):"))
        self.subject_status_label = QLabel("Non connecté")
        self.subject_status_label.setStyleSheet("color: #E74C3C;")
        subject_layout.addWidget(self.subject_status_label)
        subject_layout.addStretch()
        references_layout.addLayout(subject_layout)

        self.subject_display = QLineEdit()
        self.subject_display.setReadOnly(True)
        self.subject_display.setPlaceholderText("Aucun agent sujet connecté")
        references_layout.addWidget(self.subject_display)

        # Object display (DOIT être un QTextEdit car multiple)
        object_layout = QHBoxLayout()
        object_layout.addWidget(QLabel("Objets (Agents):"))
        self.objects_count_label = QLabel("0 connecté(s)")
        self.objects_count_label.setStyleSheet("color: gray;")
        object_layout.addWidget(self.objects_count_label)
        object_layout.addStretch()
        references_layout.addLayout(object_layout)

        self.objects_display = QTextEdit()
        self.objects_display.setReadOnly(True)
        self.objects_display.setMaximumHeight(60)
        self.objects_display.setPlaceholderText("Aucun agent objet connecté")
        references_layout.addWidget(self.objects_display)

    
        
        # Other references
        references_layout.addWidget(QLabel("Ressources impliquées:"))
        self.involved_resources_list = QListWidget()
        self.involved_resources_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        references_layout.addWidget(self.involved_resources_list)
        
        references_layout.addWidget(QLabel("Paramètres dépendants:"))
        self.depends_parameters_list = QListWidget()
        self.depends_parameters_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        references_layout.addWidget(self.depends_parameters_list)
        
        # Remplacement de l'ajout au main_layout par le retour du groupe
        # main_layout.addWidget(references_group)
        return references_group

    def _add_info_label(self, main_layout: QVBoxLayout):
        """Add informational label about flexible connectivity approach."""
        info_label = QLabel(
            "💡 L'éditeur est flexible : vous pouvez créer des processus même si les connexions "
            "obligatoires ne sont pas encore établies. Les éléments manquants seront signalés visuellement."
        )
        info_label.setStyleSheet("color: #2E86AB; background-color: #F0F8FF; padding: 8px; border-radius: 4px;")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

    def _setup_process_type_selector(self, main_layout: QVBoxLayout):
        """Setup process type selector (only enabled for creation)."""
        type_group = QGroupBox("Type de Processus")
        type_layout = QHBoxLayout(type_group)
        
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Processus de Transformation", "Processus de Mouvement"])
        #self.type_combo.addItems(["Processus", "Processus de Transformation", "Processus de Mouvement"])
        
        self.type_mapping = {
            #"Processus": "Process",
            "Processus de Transformation": "TransformationProcess", 
            "Processus de Mouvement": "MovementProcess"
        }
        
        current_display_name = next(
            (k for k, v in self.type_mapping.items() if v == self.process_type), 
            "Processus"
        )
        self.type_combo.setCurrentText(current_display_name)
        self.type_combo.setEnabled(self.process is None)
        
        if self.process is None:
            self.type_combo.currentTextChanged.connect(self._on_process_type_changed)
        
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        main_layout.addWidget(type_group)

    def _setup_form_group(self, main_layout: QVBoxLayout):
        """Setup the basic information form group."""
        form_group = QGroupBox("Informations de base")
        form_layout = QFormLayout(form_group)
        
        self._setup_id_field(form_layout)
        self._setup_name_field(form_layout)
        self._setup_equation_field(form_layout)
        self._setup_pseudocode_field(form_layout)
        self._setup_description_field(form_layout)
        self._setup_comment_field(form_layout)
        
        main_layout.addWidget(form_group)

    def _setup_id_field(self, form_layout: QFormLayout):
        """Setup the ID field (read-only)."""
        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        self.id_edit.setStyleSheet("background-color: #f0f0f0;")
        form_layout.addRow(QLabel("ID:"), self.id_edit)

    def _setup_name_field(self, form_layout: QFormLayout):
        """Setup the name field (required)."""
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nom du processus *")
        form_layout.addRow(QLabel("Nom *:"), self.name_edit)

    def _setup_equation_field(self, form_layout: QFormLayout):
        """Setup the equation field."""
        self.equation_edit = QTextEdit()
        self.equation_edit.setPlaceholderText("Équation mathématique (optionnel)")
        self.equation_edit.setMaximumHeight(60)
        form_layout.addRow(QLabel("Équation:"), self.equation_edit)

    def _setup_pseudocode_field(self, form_layout: QFormLayout):
        """Setup the pseudocode field."""
        self.pseudocode_edit = QTextEdit()
        self.pseudocode_edit.setPlaceholderText("Pseudo-code du processus (optionnel)")
        self.pseudocode_edit.setMaximumHeight(80)
        form_layout.addRow(QLabel("Pseudo-code:"), self.pseudocode_edit)

    def _setup_description_field(self, form_layout: QFormLayout):
        """Setup the description field."""
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Description détaillée du processus")
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow(QLabel("Description:"), self.description_edit)

    def _setup_comment_field(self, form_layout: QFormLayout):
        """Setup the comment field."""
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Notes et commentaires")
        self.comment_edit.setMaximumHeight(80)
        form_layout.addRow(QLabel("Commentaire:"), self.comment_edit)

    def _setup_process_specific_group(self, main_layout: QVBoxLayout):
        """Setup process-specific attributes group."""
        self.specific_group = QGroupBox("Attributs spécifiques au type de processus")
        self.specific_layout = QVBoxLayout(self.specific_group)
        
        self.stacked_widget = QStackedWidget()
        
        # Base Process
        base_widget = QWidget()
        base_layout = QVBoxLayout(base_widget)
        base_label = QLabel("Processus de base - pas d'attributs spécifiques supplémentaires.")
        base_label.setStyleSheet("color: gray; font-style: italic;")
        base_layout.addWidget(base_label)
        self.stacked_widget.addWidget(base_widget)
        
        # Transformation Process
        transformation_widget = QWidget()
        transformation_layout = QFormLayout(transformation_widget)
        self._setup_transformation_specific(transformation_layout)
        self.stacked_widget.addWidget(transformation_widget)
        
        # Movement Process  
        movement_widget = QWidget()
        movement_layout = QFormLayout(movement_widget)
        self._setup_movement_specific(movement_layout)
        self.stacked_widget.addWidget(movement_widget)
        
        self.specific_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(self.specific_group)
        
        self._update_specific_ui()

    def _setup_transformation_specific(self, layout: QFormLayout):
        """Setup TransformationProcess specific fields."""
        self.transformation_type_combo = QComboBox()
        self.transformation_type_combo.addItems(list(self.TRANSFORMATION_TYPE_MAPPING.keys()))
        layout.addRow(QLabel("Type de transformation:"), self.transformation_type_combo)
        
        layout.addRow(QLabel("Ressources affectées:"))
        self.affects_resources_list = QListWidget()
        self.affects_resources_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addRow(self.affects_resources_list)

    def _setup_movement_specific(self, layout: QFormLayout):
        """Setup MovementProcess specific fields with connection-based approach."""
        # Source agent display (read-only, based on connections)
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Agent Source *:"))
        self.source_display = QLineEdit()
        self.source_display.setReadOnly(True)
        self.source_display.setPlaceholderText("Aucun agent source connecté")
        source_layout.addWidget(self.source_display)
        
        self.source_status = QLabel("❌")
        self.source_status.setToolTip("Agent source non connecté")
        source_layout.addWidget(self.source_status)
        layout.addRow(source_layout)
        
        # Destination agent display (read-only, based on connections)
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Agent Destination *:"))
        self.destination_display = QLineEdit()
        self.destination_display.setReadOnly(True)
        self.destination_display.setPlaceholderText("Aucun agent destination connecté")
        dest_layout.addWidget(self.destination_display)
        
        self.destination_status = QLabel("❌")
        self.destination_status.setToolTip("Agent destination non connecté")
        dest_layout.addWidget(self.destination_status)
        layout.addRow(dest_layout)
        
        # Information about connectivity
        info_label = QLabel(
            "💡 <b>Connexions requises :</b><br>"
            "• Agent Source : connectez un agent en tant que <b>sujet</b><br>"
            "• Agent Destination : connectez un agent en tant qu'<b>objet</b><br>"
            "Les connexions se font via l'éditeur graphique."
        )
        info_label.setStyleSheet("color: #666; font-size: 10px; background-color: #FFF9E6; padding: 8px; border-radius: 4px;")
        info_label.setWordWrap(True)
        layout.addRow(info_label)

    def _setup_references_group(self, main_layout: QVBoxLayout):
        """Setup the references group."""
        references_group = QGroupBox("Références (Gérées par Connexions Graphiques)")
        references_layout = QVBoxLayout(references_group)
        
       # Subject display (DOIT être un QLineEdit car unique)
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Sujet (Agent):"))
        self.subject_status_label = QLabel("Non connecté")
        self.subject_status_label.setStyleSheet("color: #E74C3C;")
        subject_layout.addWidget(self.subject_status_label)
        subject_layout.addStretch()
        references_layout.addLayout(subject_layout)

        self.subject_display = QLineEdit()
        self.subject_display.setReadOnly(True)
        self.subject_display.setPlaceholderText("Aucun agent sujet connecté")
        references_layout.addWidget(self.subject_display)
        
        # Object display (DOIT être un QTextEdit car multiple)
        object_layout = QHBoxLayout()
        object_layout.addWidget(QLabel("Objets (Agents):"))
        self.objects_count_label = QLabel("0 connecté(s)")
        self.objects_count_label.setStyleSheet("color: gray;")
        object_layout.addWidget(self.objects_count_label)
        object_layout.addStretch()
        references_layout.addLayout(object_layout)

        self.objects_display = QTextEdit()
        self.objects_display.setReadOnly(True)
        self.objects_display.setMaximumHeight(60)
        self.objects_display.setPlaceholderText("Aucun agent objet connecté")
        references_layout.addWidget(self.objects_display)
                
        # Other references
        references_layout.addWidget(QLabel("Ressources impliquées:"))
        self.involved_resources_list = QListWidget()
        self.involved_resources_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        references_layout.addWidget(self.involved_resources_list)
        
        references_layout.addWidget(QLabel("Paramètres dépendants:"))
        self.depends_parameters_list = QListWidget()
        self.depends_parameters_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        references_layout.addWidget(self.depends_parameters_list)
        
        main_layout.addWidget(references_group)

    def _setup_visual_warnings_section(self, main_layout: QVBoxLayout):
        """Setup the visual warnings section."""
        self.warnings_group = QGroupBox("État de Conformité")
        warnings_layout = QVBoxLayout(self.warnings_group)
        
        self.conformity_label = QLabel("✅ Toutes les connexions requises sont établies")
        self.conformity_label.setStyleSheet("color: #27AE60; font-weight: bold; padding: 8px;")
        
        self.warnings_list = QLabel()
        self.warnings_list.setStyleSheet("color: #E74C3C; padding: 4px;")
        self.warnings_list.setWordWrap(True)
        
        warnings_layout.addWidget(self.conformity_label)
        warnings_layout.addWidget(self.warnings_list)
        
        main_layout.addWidget(self.warnings_group)

    def _setup_button_box(self, main_layout: QVBoxLayout):
        """Setup the dialog button box."""
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _on_process_type_changed(self):
        """Handle process type change during creation."""
        self._update_specific_ui()
        self._update_visual_warnings()

    def _update_specific_ui(self):
        """Update the UI based on the selected process type."""
        display_type = self.type_combo.currentText()
        ecore_type = self.type_mapping.get(display_type, "Process")
        
        stack_index = {"Process": 0, "TransformationProcess": 1, "MovementProcess": 2}
        self.stacked_widget.setCurrentIndex(stack_index.get(ecore_type, 0))
        
        titles = {
            "Process": "Processus de base",
            "TransformationProcess": "Processus de Transformation",
            "MovementProcess": "Processus de Mouvement"
        }
        self.specific_group.setTitle(f"Attributs spécifiques - {titles.get(ecore_type, 'Processus')}")

    def _update_visual_warnings(self):
        """Update visual warnings based on current connectivity state."""
        display_type = self.type_combo.currentText()
        ecore_type = self.type_mapping.get(display_type, "Process")
        
        warnings = []
        
        # Check subjects (required for all process types)
        connected_subjects = self.connected_entities.get('subjects', [])
        if not connected_subjects:
            warnings.append("• Aucun agent sujet connecté")
            self.subject_display.setStyleSheet("background-color: #FFE6E6;")
            #self.subjects_count_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        else:
            self.subject_display.setStyleSheet("background-color: #E6FFE6;")
            #self.subjects_count_label.setStyleSheet("color: #27AE60; font-weight: bold;")
        
        # Process-specific checks
        if ecore_type == "MovementProcess":
            # Check source (should be one of the connected subjects)
            source_agent = self.connected_entities.get('source')
            if source_agent and source_agent in connected_subjects:
                self.source_display.setText(f"{getattr(source_agent, 'name', 'Inconnu')} ({getattr(source_agent, 'id', 'ID')})")
                self.source_display.setStyleSheet("background-color: #E6FFE6; color: #000;")
                self.source_status.setText("✅")
                self.source_status.setToolTip("Agent source correctement connecté")
            else:
                self.source_display.setText("")
                self.source_display.setStyleSheet("background-color: #FFE6E6; color: #666;")
                self.source_status.setText("❌")
                self.source_status.setToolTip("Agent source non connecté ou invalide")
                warnings.append("• Agent source non connecté")
            
            # Check destination (should be the connected object)
            destination_agent = self.connected_entities.get('object')
            if destination_agent:
                self.destination_display.setText(f"{getattr(destination_agent, 'name', 'Inconnu')} ({getattr(destination_agent, 'id', 'ID')})")
                self.destination_display.setStyleSheet("background-color: #E6FFE6; color: #000;")
                self.destination_status.setText("✅")
                self.destination_status.setToolTip("Agent destination correctement connecté")
                #self.object_status_label.setText("Connecté")
                #self.object_status_label.setStyleSheet("color: #27AE60; font-weight: bold;")
            else:
                self.destination_display.setText("")
                self.destination_display.setStyleSheet("background-color: #FFE6E6; color: #666;")
                self.destination_status.setText("❌")
                self.destination_status.setToolTip("Agent destination non connecté")
                #self.object_status_label.setText("Non connecté")
                #self.object_status_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
                warnings.append("• Agent destination non connecté")
            
            # Check if source and destination are different
            if source_agent and destination_agent and source_agent == destination_agent:
                warnings.append("• L'agent source et destination sont identiques")
        
        # Update warnings display
        if warnings:
            self.conformity_label.setText("⚠️ Connexions requises manquantes")
            self.conformity_label.setStyleSheet("color: #E67E22; font-weight: bold; padding: 8px; background-color: #FFF9E6;")
            self.warnings_list.setText("\n".join(warnings))
            self.warnings_group.setStyleSheet("QGroupBox { border: 2px solid #E67E22; }")
        else:
            self.conformity_label.setText("✅ Toutes les connexions requises sont établies")
            self.conformity_label.setStyleSheet("color: #27AE60; font-weight: bold; padding: 8px; background-color: #E6FFE6;")
            self.warnings_list.setText("")
            self.warnings_group.setStyleSheet("QGroupBox { border: 2px solid #27AE60; }")
        
        # Update references display
        self._update_references_display()

    def _update_references_display(self):
        """Update the references display with current connections."""
        # Objets display (MULTIPLE - QTextEdit)
        connected_objects = self.connected_entities.get('objects', [])
        if connected_objects:
            objects_text = "\n".join([
                f"• {getattr(agent, 'name', 'Inconnu')} ({getattr(agent, 'id', 'ID')})"
                for agent in connected_objects
            ])
            self.objects_display.setPlainText(objects_text)
            self.objects_count_label.setText(f"{len(connected_objects)} connecté(s)")
        else:
            self.objects_display.setPlainText("")
            self.objects_count_label.setText("0 connecté(s)")
        
        # Sujet display (UNIQUE - QLineEdit)
        connected_subject = self.connected_entities.get('subject')
        if connected_subject:
            self.subject_display.setText(f"{getattr(connected_subject, 'name', 'Inconnu')} ({getattr(connected_subject, 'id', 'ID')})")
            self.subject_status_label.setText("Connecté")
            self.subject_status_label.setStyleSheet("color: #27AE60;")
        else:
            self.subject_display.setText("")
            self.subject_status_label.setText("Non connecté")
            self.subject_status_label.setStyleSheet("color: #E74C3C;")
    
    # --- Data Handling Methods ---

    def _generate_process_id(self) -> str:
        """Generate a unique process ID."""
        base_id = "process_"
        counter = 1
        while f"{base_id}{counter:03d}" in self.existing_ids:
            counter += 1
        return f"{base_id}{counter:03d}"

    def _load_data(self):
        """Load data from process object or initialize with default values."""
        self._populate_reference_lists()
        
        if self.process:
            self._load_existing_process_data()
        else:
            self._initialize_new_process_data()
        
        self._update_visual_warnings()

    def _populate_reference_lists(self):
        """Populate reference lists with available entities."""
        # Involved Resources list
        self.involved_resources_list.clear()
        for resource in self.current_resources:
            resource_id = getattr(resource, 'id', 'ID Inconnu')
            resource_name = getattr(resource, 'name', 'Nom Inconnu')
            item = QListWidgetItem(f"{resource_name} ({resource_id})")
            item.setData(Qt.UserRole, resource)
            self.involved_resources_list.addItem(item)
        
        # Depends on Parameters list
        self.depends_parameters_list.clear()
        for parameter in self.current_parameters:
            parameter_id = getattr(parameter, 'id', 'ID Inconnu')
            parameter_name = getattr(parameter, 'name', 'Nom Inconnu')
            item = QListWidgetItem(f"{parameter_name} ({parameter_id})")
            item.setData(Qt.UserRole, parameter)
            self.depends_parameters_list.addItem(item)
        
        # Affects Resources list (for TransformationProcess)
        if hasattr(self, 'affects_resources_list'):
            self.affects_resources_list.clear()
            for resource in self.current_resources:
                resource_id = getattr(resource, 'id', 'ID Inconnu')
                resource_name = getattr(resource, 'name', 'Nom Inconnu')
                item = QListWidgetItem(f"{resource_name} ({resource_id})")
                item.setData(Qt.UserRole, resource)
                self.affects_resources_list.addItem(item)

    def _load_existing_process_data(self):
        """Load data from existing process for editing."""
        # Basic fields
        self.id_edit.setText(getattr(self.process, 'id', ''))
        self.name_edit.setText(getattr(self.process, 'name', ''))
        self.equation_edit.setPlainText(getattr(self.process, 'equation', ''))
        self.pseudocode_edit.setPlainText(getattr(self.process, 'pseudoCode', ''))
        self.description_edit.setPlainText(getattr(self.process, 'description', ''))
        self.comment_edit.setPlainText(getattr(self.process, 'comment', ''))
        
        # References from the model (for lists that allow selection)
        self._select_reference_items(self.involved_resources_list, getattr(self.process, 'involvedResources', []))
        self._select_reference_items(self.depends_parameters_list, getattr(self.process, 'dependsOnParameters', []))
        
        # Type-specific data
        if self.process_type == "TransformationProcess":
            transformation_type = getattr(self.process, 'transformationType', None)
            if transformation_type:
                type_name = getattr(transformation_type, 'name', 'Production')
                display_name = next(
                    (k for k, v in self.TRANSFORMATION_TYPE_MAPPING.items() if v == type_name),
                    "Production"
                )
                self.transformation_type_combo.setCurrentText(display_name)
            
            self._select_reference_items(self.affects_resources_list, getattr(self.process, 'affectsResources', []))

    def _initialize_new_process_data(self):
        """Initialize data for new process creation."""
        new_id = self._generate_process_id()
        self.id_edit.setText(new_id)
        self.name_edit.setText("")
        self.equation_edit.setPlainText("")
        self.pseudocode_edit.setPlainText("")
        self.description_edit.setPlainText("")
        self.comment_edit.setPlainText("")
        
        if hasattr(self, 'transformation_type_combo'):
            self.transformation_type_combo.setCurrentText("Production")

    def _select_reference_items(self, list_widget: QListWidget, entities: list):
        """Select items in a list widget based on connected entities."""
        entity_ids = {getattr(e, 'id', None) for e in entities}
        
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            entity = item.data(Qt.UserRole)
            if getattr(entity, 'id', None) in entity_ids:
                item.setSelected(True)

    def _save_initial_values(self):
        """Save initial values for Undo/Redo commands."""
        # Implementation similar to other dialogs
        pass

    # --- Validation and Acceptance Methods ---

    def _validate_data(self) -> bool:
        """Perform flexible validation - warn but don't block."""
        if not self.name_edit.text().strip():
            QMessageBox.critical(self, "Validation", "Le nom est obligatoire.")
            return False
        
        # Show warning for missing required connections but don't block
        display_type = self.type_combo.currentText()
        ecore_type = self.type_mapping.get(display_type, "Process")
        
        if ecore_type == "MovementProcess":
            source_agent = self.connected_entities.get('source')
            destination_agent = self.connected_entities.get('object')
            
            if not source_agent or not destination_agent:
                reply = QMessageBox.warning(
                    self,
                    "Connexions Manquantes",
                    "Ce processus de mouvement nécessite des connexions à un agent source et destination.\n\n"
                    "Souhaitez-vous quand même sauvegarder ?\n"
                    "Vous pourrez établir les connexions plus tard via l'éditeur graphique.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                return reply == QMessageBox.Yes
        
        return True

    def get_data(self) -> dict:
        """Collect all form data."""
        display_type = self.type_combo.currentText()
        ecore_type = self.type_mapping.get(display_type, "Process")
        
        data = {
            "id": self.id_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "equation": self.equation_edit.toPlainText().strip(),
            "pseudoCode": self.pseudocode_edit.toPlainText().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "comment": self.comment_edit.toPlainText().strip(),
            "involvedResources": self._get_selected_entities(self.involved_resources_list),
            "dependsOnParameters": self._get_selected_entities(self.depends_parameters_list),
            "process_type": ecore_type,
            'subject': self._resolve_single_subject(),
            'objects': self._resolve_objects(),
        }
        
        # Type-specific data
        if ecore_type == "TransformationProcess":
            transformation_display = self.transformation_type_combo.currentText()
            transformation_ecore = self.TRANSFORMATION_TYPE_MAPPING.get(transformation_display, "Production")
            data["transformationType"] = transformation_ecore
            data["affectsResources"] = self._get_selected_entities(self.affects_resources_list)
            
        elif ecore_type == "MovementProcess":
            # Source and destination come from connections, not from UI selection
            data["source"] = self.connected_entities.get('source')
            data["destination"] = self.connected_entities.get('object')
        
        return data

    def _resolve_single_subject(self):
        """
        Resolve the single subject with ultra-robust proxy handling.
        Returns the subject or None if not resolvable.
        """
        if not self.process:
            return None
        
        try:
            # APPROCHE 1 : Vérifier si subjects est un proxy non itérable
            if hasattr(self.process.subjects, 'eIsProxy') and self.process.subjects.eIsProxy():
                # C'est un proxy - essayer de le résoudre
                try:
                    resolved = self.process.subjects.eResource.getEObject(self.process.subjects._internal_id)
                    return resolved if resolved else None
                except:
                    print("⚠️ Impossible de résoudre le proxy du sujet")
                    return None
            
            # APPROCHE 2 : Vérifier si c'est une collection normale
            elif hasattr(self.process.subjects, '__iter__'):
                # C'est itérable - prendre le premier élément
                for subject in self.process.subjects:
                    return subject  # Retourne le premier sujet trouvé
                return None  # Collection vide
            
            # APPROCHE 3 : C'est peut-être directement l'objet
            else:
                return self.process.subjects
                
        except Exception as e:
            print(f"⚠️ Erreur lors de la résolution du sujet: {e}")
            return None

    def _resolve_objects(self):
        """Resolve objects with robust proxy handling."""
        if not self.process or not hasattr(self.process, 'objects'):
            return []
        
        try:
            # Vérifier si objects est un proxy
            if hasattr(self.process.objects, 'eIsProxy') and self.process.objects.eIsProxy():
                try:
                    resolved = self.process.objects.eResource.getEObject(self.process.objects._internal_id)
                    return [resolved] if resolved else []
                except:
                    return []
            
            # Vérifier si c'est itérable
            elif hasattr(self.process.objects, '__iter__'):
                resolved_objects = []
                for obj in self.process.objects:
                    if hasattr(obj, 'eIsProxy') and obj.eIsProxy():
                        try:
                            resolved_obj = obj.eResource.getEObject(obj._internal_id)
                            if resolved_obj:
                                resolved_objects.append(resolved_obj)
                        except:
                            continue
                    else:
                        resolved_objects.append(obj)
                return resolved_objects
            
            else:
                return [self.process.objects] if self.process.objects else []
                
        except Exception as e:
            print(f"⚠️ Erreur lors de la résolution des objets: {e}")
            return []


    def _get_selected_entities(self, list_widget: QListWidget) -> list:
        """Get list of selected Ecore objects from a QListWidget."""
        return [
            list_widget.item(i).data(Qt.UserRole)
            for i in range(list_widget.count())
            if list_widget.item(i).isSelected()
        ]

    def accept(self):
        """Handle dialog acceptance with flexible validation."""
        if not self._validate_data():
            return
            
        new_values = self.get_data()

        if self.process is None:
            self._handle_process_creation(new_values)
        else:
            self._handle_process_edition(new_values)

    def _handle_process_creation(self, new_values: dict):
        """Handle process creation logic."""
        try:
            process_type = new_values.get("process_type", "Process")
            
            if process_type == "TransformationProcess":
                self.process = self.parent().model_manager._create_transformation_process(new_values)
            elif process_type == "MovementProcess":
                self.process = self.parent().model_manager._create_movement_process(new_values)
            else:
                self.process = self.parent().model_manager.create_process(new_values)
                
            if self.process is None:
                raise ValueError("Échec de la création du Processus.")
            
            self._finalize_dialog()
            super().accept()
            
        except Exception as error:
            QMessageBox.critical(
                self, 
                "Erreur", 
                f"Échec de la création du Processus : {str(error)}"
            )

    def _handle_process_edition(self, new_values: dict):
        """Handle process edition logic."""
        self._finalize_dialog()
        super().accept()

    def _finalize_dialog(self):
        """Perform cleanup and notification operations."""
        if hasattr(self.parent(), 'update_navigation_tree'):
            self.parent().update_navigation_tree()
            
        if hasattr(self.parent(), 'model_manager') and hasattr(self.parent().model_manager, 'save_model'):
            self.parent().model_manager.save_model()