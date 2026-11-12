"""
Dialog for editing or creating Agent elements.
Handles AgentType enumeration and complex references.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QTextEdit, QMessageBox, QLabel,
    QListWidget, QAbstractItemView, QComboBox, QListWidgetItem,
    QPushButton, QHBoxLayout, QGroupBox, QWidget
)
from PySide6.QtCore import Qt
from pyecore.ecore import EObject, EEnumLiteral

import sys
from pathlib import Path

# Configure path for root modules (e.g., commands.py)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from commands import ModifyFieldCommand


class AgentDialog(QDialog):
    """
    Dialog for editing or creating Agent elements.
    
    This dialog handles:
    - Basic agent information (id, name, type, description, comment)
    - Complex references (holdsResources, isSubjectOf, isObjectOf)
    - AgentType enumeration management
    - Undo/Redo command integration
    
    Attributes:
        AGENT_TYPE_MAPPING (dict): Mapping between display labels and Ecore enum names
        REFERENCE_FIELDS (list): List of reference fields managed in the dialog
    """
    
    # Mapping between display labels and Ecore enumeration names for AgentType
    AGENT_TYPE_MAPPING = {
        "Humain": "Human", 
        "Biologique": "Biological", 
        "Physique": "Physical", 
        "Social": "Social"
    }
    
    # Fields for reference lists (managed in reference UI and data methods)
    REFERENCE_FIELDS = ['holdsResources', 'isSubjectOf', 'isObjectOf', 'containsAgents']

    def __init__(
        self, 
        agent: EObject = None, 
        parent=None, 
        existing_ids=None, 
        current_properties=None, 
        current_processes=None, 
        current_resources=None, 
        connected_entities=None,
        main_window=None
    ):
        """
        Initialize the AgentDialog.
        
        Args:
            agent: Existing agent object to edit, or None for creation
            parent: Parent widget
            existing_ids: List of existing agent IDs for uniqueness validation
            current_properties: List of available properties
            current_processes: List of available processes  
            current_resources: List of available resources
            connected_entities: Dictionary of pre-connected entities
        """
        super().__init__(parent)

        self.main_window = main_window or parent
        
        self.agent = agent
        self.old_values = {}
        self.existing_ids = existing_ids or []
        self.current_properties = current_properties or []
        self.current_processes = current_processes or []
        self.current_resources = current_resources or []
        self.connected_entities = connected_entities or {
            'holdsResources': [], 
            'isSubjectOf': [], 
            'isObjectOf': [],
            'containsAgents': [],
            'partOfParentAgent': None
        }
        self.updating_lists = False

        self._setup_dialog_configuration()
        self._initialize_data()
        self._init_ui()
        self._load_data()
        self._save_initial_values()

    def _setup_dialog_configuration(self):
        """Configure basic dialog settings."""
        self.setWindowTitle("Éditer Agent" if self.agent else "Nouvel Agent")
        self.resize(550, 700)  # Augmenté pour accommoder les nouvelles sections

    def _initialize_data(self):
        """Update existing IDs for uniqueness in creation mode."""
        if self.agent and getattr(self.agent, 'id', None) in self.existing_ids:
            self.existing_ids.remove(self.agent.id)

    # --- UI Setup Methods ---

    def _init_ui(self):
        """Initialize the main user interface."""
        main_layout = QVBoxLayout(self)
        
        self._add_info_label(main_layout)
        self._setup_form_group(main_layout)
        self._setup_references_ui(main_layout)
        self._setup_hierarchy_info_section(main_layout)  # Nouvelle section pour la hiérarchie
        self._setup_button_box(main_layout)

    def _add_info_label(self, main_layout: QVBoxLayout):
        """Add informational label about required fields."""
        info_label = QLabel("Les champs marqués d'un * sont obligatoires.")
        info_label.setStyleSheet("color: blue;")
        main_layout.addWidget(info_label)

    def _setup_form_group(self, main_layout: QVBoxLayout):
        """Setup the basic information form group."""
        form_group = QGroupBox("Informations de base")
        form_layout = QFormLayout(form_group)
        
        self._setup_id_field(form_layout)
        self._setup_name_field(form_layout)
        self._setup_type_field(form_layout)
        self._setup_description_field(form_layout)
        self._setup_comment_field(form_layout)
        
        main_layout.addWidget(form_group)

    def _setup_id_field(self, form_layout: QFormLayout):
        """Setup the ID field (read-only)."""
        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        form_layout.addRow(QLabel("ID:"), self.id_edit)

    def _setup_name_field(self, form_layout: QFormLayout):
        """Setup the name field (required)."""
        self.name_edit = QLineEdit()
        form_layout.addRow(QLabel("Nom *:"), self.name_edit)

    def _setup_type_field(self, form_layout: QFormLayout):
        """Setup the agent type combo box (required)."""
        self.type_combo = QComboBox()
        self.type_combo.addItems(list(self.AGENT_TYPE_MAPPING.keys()))
        form_layout.addRow(QLabel("Type *:"), self.type_combo)

    def _setup_description_field(self, form_layout: QFormLayout):
        """Setup the description text edit."""
        self.doc_edit = QTextEdit()
        self.doc_edit.setPlaceholderText("Description détaillée de l'agent...")
        form_layout.addRow(QLabel("Description:"), self.doc_edit)

    def _setup_comment_field(self, form_layout: QFormLayout):
        """Setup the comment text edit."""
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Commentaires internes...")
        form_layout.addRow(QLabel("Commentaire:"), self.comment_edit)

    def _setup_references_ui(self, main_layout: QVBoxLayout):
        """Setup the references section with list widgets."""
        references_group = QGroupBox("Références aux Entités")
        refs_layout = QVBoxLayout(references_group)
        
        self._setup_resources_reference(refs_layout)
        self._setup_subject_of_reference(refs_layout)
        self._setup_object_of_reference(refs_layout)
        
        main_layout.addWidget(references_group)

    def _setup_resources_reference(self, refs_layout: QVBoxLayout):
        """Setup the holdsResources reference list."""
        refs_layout.addWidget(QLabel("Ressources Détenues (holdsResources):"))
        self.resources_list = QListWidget()
        self.resources_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        refs_layout.addWidget(self.resources_list)

    def _setup_subject_of_reference(self, refs_layout: QVBoxLayout):
        """Setup the isSubjectOf reference list."""
        refs_layout.addWidget(QLabel("Sujet de Processus (isSubjectOf):"))
        self.subject_of_list = QListWidget()
        self.subject_of_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        refs_layout.addWidget(self.subject_of_list)

    def _setup_object_of_reference(self, refs_layout: QVBoxLayout):
        """Setup the isObjectOf reference list."""
        refs_layout.addWidget(QLabel("Objet de Processus (isObjectOf):"))
        self.object_of_list = QListWidget()
        self.object_of_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        refs_layout.addWidget(self.object_of_list)

    def _setup_hierarchy_info_section(self, main_layout: QVBoxLayout):
        """
        Setup hierarchy information section (read-only).
        
        Note: Agent hierarchy (containsAgents/partOfParentAgent) is managed
        through graphical connectors for better UX, not through this dialog.
        """
        hierarchy_group = QGroupBox("Hiérarchie des Agents (Gérée par Connecteurs Graphiques)")
        hierarchy_layout = QVBoxLayout(hierarchy_group)
        
        # Parent agent info (read-only)
        parent_info_layout = QHBoxLayout()
        parent_info_layout.addWidget(QLabel("Agent Parent:"))
        self.parent_agent_label = QLabel("Aucun")
        self.parent_agent_label.setStyleSheet("font-style: italic; color: gray;")
        parent_info_layout.addWidget(self.parent_agent_label)
        parent_info_layout.addStretch()
        hierarchy_layout.addLayout(parent_info_layout)
        
        # Contained agents info (read-only)
        hierarchy_layout.addWidget(QLabel("Agents Contenus:"))
        self.contained_agents_label = QLabel("Aucun")
        self.contained_agents_label.setStyleSheet("font-style: italic; color: gray;")
        self.contained_agents_label.setWordWrap(True)
        hierarchy_layout.addWidget(self.contained_agents_label)
        
        # Information note
        info_note = QLabel(
            "💡 La hiérarchie d'agents est gérée visuellement par des connecteurs "
            "graphiques dans l'éditeur, pas dans ce dialogue."
        )
        info_note.setStyleSheet("color: blue; font-size: 10px;")
        info_note.setWordWrap(True)
        hierarchy_layout.addWidget(info_note)
        
        main_layout.addWidget(hierarchy_group)

    def _setup_button_box(self, main_layout: QVBoxLayout):
        """Setup the dialog button box."""
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    # --- Data Handling Methods ---

    def _generate_agent_id(self) -> str:
        """
        Generate a unique agent ID in format 'agent_XXX'.
        
        Returns:
            str: Unique agent ID
        """
        base_id = "agent_"
        counter = 1
        while f"{base_id}{counter:03d}" in self.existing_ids:
            counter += 1
        return f"{base_id}{counter:03d}"

    def _get_type_label_from_enum(self, enum_value: EObject) -> str:
        """
        Convert Ecore enumeration value to display label.
        
        Args:
            enum_value: Ecore enumeration value
            
        Returns:
            str: Display label for the enumeration
        """
        if not enum_value:
            return "Humain"
            
        enum_name = getattr(enum_value, 'name', None)
        return next(
            (label for label, name in self.AGENT_TYPE_MAPPING.items() if name == enum_name), 
            "Humain"
        )

    def _load_data(self):
        """Load data from agent object or initialize with default values."""
        if self.agent:
            self._load_existing_agent_data()
        else:
            self._initialize_new_agent_data()
        
        # Mettre à jour les informations de hiérarchie
        self._update_hierarchy_display()

    def _load_existing_agent_data(self):
        """Load data from existing agent for editing."""
        # Basic fields
        self.id_edit.setText(getattr(self.agent, 'id', ''))
        self.name_edit.setText(getattr(self.agent, 'name', ''))
        self.doc_edit.setPlainText(getattr(self.agent, 'description', ''))
        self.comment_edit.setPlainText(getattr(self.agent, 'comment', ''))
        
        # Type field
        agent_type_enum = getattr(self.agent, 'type', None)
        type_label = self._get_type_label_from_enum(agent_type_enum)
        index = self.type_combo.findText(type_label)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        # Reference fields
        self._populate_reference_list(
            self.resources_list, 
            self.current_resources, 
            getattr(self.agent, 'holdsResources', [])
        )
        self._populate_reference_list(
            self.subject_of_list, 
            self.current_processes, 
            getattr(self.agent, 'isSubjectOf', [])
        )
        self._populate_reference_list(
            self.object_of_list, 
            self.current_processes, 
            getattr(self.agent, 'isObjectOf', [])
        )

    def _initialize_new_agent_data(self):
        """Initialize data for new agent creation."""
        new_id = self._generate_agent_id()
        self.id_edit.setText(new_id)
        self.name_edit.setText("")
        self.doc_edit.setPlainText("")
        self.comment_edit.setPlainText("")
        self.type_combo.setCurrentText("Humain")

        # Initialize reference lists
        self._populate_reference_list(self.resources_list, self.current_resources, [])
        self._populate_reference_list(self.subject_of_list, self.current_processes, [])
        self._populate_reference_list(self.object_of_list, self.current_processes, [])

    def _update_hierarchy_display(self):
        """Update the hierarchy information display with current data."""
        # Parent agent
        parent_agent = getattr(self.agent, 'partOfParentAgent', None) if self.agent else None
        if parent_agent:
            parent_name = getattr(parent_agent, 'name', 'Sans nom')
            parent_id = getattr(parent_agent, 'id', 'ID inconnu')
            self.parent_agent_label.setText(f"{parent_name} ({parent_id})")
            self.parent_agent_label.setStyleSheet("")
        else:
            self.parent_agent_label.setText("Aucun")
            self.parent_agent_label.setStyleSheet("font-style: italic; color: gray;")
        
        # Contained agents
        contained_agents = getattr(self.agent, 'containsAgents', []) if self.agent else []
        if contained_agents:
            contained_names = [
                f"{getattr(agent, 'name', 'Sans nom')} ({getattr(agent, 'id', 'ID inconnu')})"
                for agent in contained_agents
            ]
            self.contained_agents_label.setText(", ".join(contained_names))
            self.contained_agents_label.setStyleSheet("")
        else:
            self.contained_agents_label.setText("Aucun")
            self.contained_agents_label.setStyleSheet("font-style: italic; color: gray;")

    def _populate_reference_list(
        self, 
        list_widget: QListWidget, 
        all_entities: list, 
        connected_entities: list
    ):
        """
        Populate a QListWidget with available entities and select connected ones.
        
        Args:
            list_widget: The list widget to populate
            all_entities: All available entities for this reference
            connected_entities: Currently connected entities
        """
        if not self.parent():
            return
            
        list_widget.clear()
        
        connected_ids = {
            getattr(entity, 'id', None) 
            for entity in connected_entities 
            if entity is not None
        }
        
        for entity in all_entities:
            entity_id = getattr(entity, 'id', 'ID Inconnu')
            entity_name = getattr(entity, 'name', 'Nom Inconnu')
            
            item = QListWidgetItem(f"{entity_name} ({entity_id})")
            item.setData(Qt.UserRole, entity)
            
            if entity_id in connected_ids:
                item.setSelected(True)
                
            list_widget.addItem(item)

    def _save_initial_values(self):
        """Save initial values for Undo/Redo commands."""
        type_label = self.type_combo.currentText()
        type_enum_name = self.AGENT_TYPE_MAPPING.get(type_label, "Human")
        
        self.old_values = {
            "id": self.id_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "type": type_enum_name,
            "description": self.doc_edit.toPlainText().strip(),
            "comment": self.comment_edit.toPlainText().strip(),
            "holdsResources": [
                getattr(entity, 'id') 
                for entity in getattr(self.agent, 'holdsResources', [])
            ],
            "isSubjectOf": [
                getattr(entity, 'id') 
                for entity in getattr(self.agent, 'isSubjectOf', [])
            ],
            "isObjectOf": [
                getattr(entity, 'id') 
                for entity in getattr(self.agent, 'isObjectOf', [])
            ],
            "containsAgents": [
                getattr(entity, 'id')
                for entity in getattr(self.agent, 'containsAgents', [])
            ],
        }

    # --- Validation and Acceptance Methods ---

    def _validate_data(self) -> bool:
        """
        Perform all data validation.
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        return (
            self._validate_name() and 
            self._validate_type() and 
            self._validate_id()
        )

    def _validate_name(self) -> bool:
        """Validate the name field."""
        if not self.name_edit.text().strip():
            QMessageBox.critical(self, "Erreur de validation", "Le Nom (*) ne peut pas être vide.")
            self.name_edit.setFocus()
            return False
        return True

    def _validate_type(self) -> bool:
        """Validate the type field."""
        type_label = self.type_combo.currentText().strip()
        if not type_label or type_label not in self.AGENT_TYPE_MAPPING:
            QMessageBox.critical(self, "Erreur de validation", "Le Type (*) ne peut pas être vide ou est invalide.")
            self.type_combo.setFocus()
            return False
        return True

    def _validate_id(self) -> bool:
        """Validate the ID field."""
        new_id = self.id_edit.text().strip()
        if self.agent is None and new_id in self.existing_ids:
            QMessageBox.critical(self, "Erreur de validation", f"L'ID '{new_id}' est déjà utilisé.")
            return False
        return True

    
    def _get_enum_literal(self, enum_name: str, enum_type: str):
        """Récupère le literal d'enum correspondant."""
        try:
            
            if enum_type == 'AgentType':
                enum_class = self.main_window.model_manager._ecore_classes['AgentType']
            elif enum_type == 'TransformationType':
                enum_class = self.main_window.model_manager._ecore_classes['TransformationType']
            else:
                return None
                
            literal = enum_class.getEEnumLiteral(enum_name)
            return literal
            
        except Exception as e:
            print(f"❌ ERREUR _get_enum_literal: {e}")
            return None

    def get_data(self) -> dict:
        """
        Collect all form data including EEnumLiterals and references.
        
        Returns:
            dict: All collected form data
        """

        type_label = self.type_combo.currentText()
        type_enum_name = self.AGENT_TYPE_MAPPING.get(type_label, "Human") 
        type_enum_literal = self._get_enum_literal(type_enum_name, 'AgentType')
        
        return {
            "id": self.id_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "type": type_enum_literal,
            "description": self.doc_edit.toPlainText().strip(),
            "comment": self.comment_edit.toPlainText().strip(),
            "holdsResources": self._get_selected_entities(self.resources_list),
            "isSubjectOf": self._get_selected_entities(self.subject_of_list),
            "isObjectOf": self._get_selected_entities(self.object_of_list),
            # containsAgents et partOfParentAgent sont gérés par connecteurs, pas par ce dialogue
        }

    def _get_selected_entities(self, list_widget: QListWidget) -> list:
        """
        Get list of selected Ecore objects from a QListWidget.
        
        Args:
            list_widget: The list widget to get selections from
            
        Returns:
            list: List of selected Ecore objects
        """
        return [
            list_widget.item(i).data(Qt.UserRole)
            for i in range(list_widget.count())
            if list_widget.item(i).isSelected()
        ]

    def accept(self):
        """Handle dialog acceptance with validation and command execution."""
        if not self._validate_data():
            return
            
        new_values = self.get_data()

        if self.agent is None:
            self._handle_agent_creation(new_values)
        else:
            self._handle_agent_edition(new_values)

    def _handle_agent_creation(self, new_values: dict):
        """Handle agent creation logic."""
        try:
            self.agent = self.parent().model_manager.create_agent(new_values)
            if self.agent is None:
                raise ValueError("Échec de la création de l'Agent.")
            
            self._finalize_dialog()
            super().accept()
            
        except Exception as error:
            QMessageBox.critical(
                self, 
                "Erreur", 
                f"Échec de la création de l'Agent : {str(error)}"
            )

    def _handle_agent_edition(self, new_values: dict):
        """Handle agent edition logic."""
        self._execute_model_commands(new_values)
        self._finalize_dialog()
        super().accept()

    def _execute_model_commands(self, new_values: dict):
        """
        Create and execute ModifyFieldCommand for modified fields.
        
        Args:
            new_values: New values from the form
        """
        if self.agent is None or not hasattr(self.parent(), 'execute_command'):
            return

        field_mapping = {
            "name": "name", 
            "description": "description", 
            "comment": "comment", 
            "type": "type",
            "holdsResources": "holdsResources",
            "isSubjectOf": "isSubjectOf",
            "isObjectOf": "isObjectOf",
            # containsAgents est géré par connecteurs, pas par commandes standards
        }

        for ecore_field_name, data_key in field_mapping.items():
            if self._is_field_modified(data_key, new_values):
                command = ModifyFieldCommand(
                    self.parent(), 
                    self.agent, 
                    ecore_field_name,
                    self.old_values.get(data_key, ''),
                    new_values.get(data_key)
                )
                self.parent().execute_command(command)

    def _is_field_modified(self, data_key: str, new_values: dict) -> bool:
        """
        Check if a field has been modified.
        
        Args:
            data_key: The field key to check
            new_values: New values dictionary
            
        Returns:
            bool: True if the field has been modified
        """
        old_value = self.old_values.get(data_key, '')
        new_value = new_values.get(data_key)
        
        if data_key == "type":
            new_value_for_comparison = getattr(new_value, 'name', None)
        elif data_key in self.REFERENCE_FIELDS:
            new_value_for_comparison = [
                getattr(entity, 'id') 
                for entity in new_value
            ]
        else:
            new_value_for_comparison = new_value

        if isinstance(new_value_for_comparison, list):
            return set(old_value) != set(new_value_for_comparison)
        else:
            return old_value != new_value_for_comparison

    def _finalize_dialog(self):
        """Perform cleanup and notification operations after successful acceptance."""
        if hasattr(self.parent(), 'update_navigation_tree'):
            self.parent().update_navigation_tree()
            
        if hasattr(self.parent(), 'model_manager') and hasattr(self.parent().model_manager, 'save_model'):
            self.parent().model_manager.save_model()