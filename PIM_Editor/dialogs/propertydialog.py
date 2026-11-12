"""
Dialog for editing or creating Parameter elements.
Parameter inherits from Property which inherits from NamedElement.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QTextEdit, QMessageBox, QLabel, QHBoxLayout, QPushButton,
    QGroupBox, QCheckBox
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


class ParameterDialog(QDialog):
    """
    Dialog for editing or creating Parameter elements.
    
    This dialog handles:
    - Basic parameter information (id, name, description, comment, unit)
    - Parameter-specific attributes (value, isExogenous, parameterType)
    - Integration with Undo/Redo system
    
    According to the metamodel, Parameter inherits from Property which inherits from NamedElement.
    """

    def __init__(
        self, 
        parameter: EObject = None, 
        parent=None, 
        existing_ids=None
    ):
        """
        Initialize the ParameterDialog.
        
        Args:
            parameter: Existing parameter object to edit, or None for creation
            parent: Parent widget
            existing_ids: List of existing parameter IDs for uniqueness validation
        """
        super().__init__(parent)
        
        
        self.parameter = parameter
        self.old_values = {}
        self.existing_ids = existing_ids or []
        
        self._setup_dialog_configuration()
        self._init_ui()
        self._load_data()
        self._save_initial_values()

    def _setup_dialog_configuration(self):
        """Configure basic dialog settings."""
        self.setWindowTitle("Éditer Paramètre" if self.parameter else "Nouveau Paramètre")
        self.resize(400, 500)

    def _init_ui(self):
        """Initialize the main user interface."""
        main_layout = QVBoxLayout(self)
        
        self._add_info_label(main_layout)
        self._setup_form_group(main_layout)
        self._setup_parameter_specific_group(main_layout)
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
        self._setup_unit_field(form_layout)
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
        self.name_edit.setPlaceholderText("Nom du paramètre *")
        form_layout.addRow(QLabel("Nom *:"), self.name_edit)

    def _setup_unit_field(self, form_layout: QFormLayout):
        """Setup the unit field."""
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("Unité (ex: kg, m², unités)")
        form_layout.addRow(QLabel("Unité:"), self.unit_edit)

    def _setup_description_field(self, form_layout: QFormLayout):
        """Setup the description text edit."""
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Description détaillée du paramètre")
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow(QLabel("Description:"), self.description_edit)

    def _setup_comment_field(self, form_layout: QFormLayout):
        """Setup the comment text edit."""
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Notes et commentaires")
        self.comment_edit.setMaximumHeight(80)
        form_layout.addRow(QLabel("Commentaire:"), self.comment_edit)

    def _setup_parameter_specific_group(self, main_layout: QVBoxLayout):
        """Setup the parameter-specific attributes group."""
        param_group = QGroupBox("Attributs spécifiques au Paramètre")
        param_layout = QFormLayout(param_group)
        
        self._setup_value_field(param_layout)
        self._setup_parameter_type_field(param_layout)
        self._setup_exogenous_field(param_layout)
        
        main_layout.addWidget(param_group)

    def _setup_value_field(self, param_layout: QFormLayout):
        """Setup the value field."""
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Valeur du paramètre (ex: 100, true, 'texte')")
        param_layout.addRow(QLabel("Valeur:"), self.value_edit)

    def _setup_parameter_type_field(self, param_layout: QFormLayout):
        """Setup the parameter type field."""
        self.parameter_type_combo = QComboBox()
        self.parameter_type_combo.addItems([
            "integer", "float", "boolean", "string", "expression"
        ])
        self.parameter_type_combo.setCurrentText("float")  # Valeur par défaut
        param_layout.addRow(QLabel("Type de paramètre:"), self.parameter_type_combo)

    def _setup_exogenous_field(self, param_layout: QFormLayout):
        """Setup the exogenous checkbox."""
        self.exogenous_checkbox = QCheckBox("Paramètre exogène")
        self.exogenous_checkbox.setToolTip("Si coché, ce paramètre est considéré comme exogène au modèle")
        param_layout.addRow("", self.exogenous_checkbox)

    def _setup_button_box(self, main_layout: QVBoxLayout):
        """Setup the dialog button box."""
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    # --- Data Handling Methods ---

    def _generate_parameter_id(self) -> str:
        """
        Generate a unique parameter ID in format 'parameter_XXX'.
        
        Returns:
            str: Unique parameter ID
        """
        base_id = "parameter_"
        counter = 1
        while f"{base_id}{counter:03d}" in self.existing_ids:
            counter += 1
        return f"{base_id}{counter:03d}"

    def _load_data(self):
        """Load data from parameter object or initialize with default values."""
        if self.parameter:
            self._load_existing_parameter_data()
        else:
            self._initialize_new_parameter_data()

    def _load_existing_parameter_data(self):
        """Load data from existing parameter for editing."""
        # Basic fields from NamedElement
        self.id_edit.setText(getattr(self.parameter, 'id', ''))
        self.name_edit.setText(getattr(self.parameter, 'name', ''))
        self.description_edit.setPlainText(getattr(self.parameter, 'description', ''))
        self.comment_edit.setPlainText(getattr(self.parameter, 'comment', ''))
        
        # Property field
        self.unit_edit.setText(getattr(self.parameter, 'unit', ''))
        
        # Parameter-specific fields
        self.value_edit.setText(getattr(self.parameter, 'value', ''))
        
        parameter_type = getattr(self.parameter, 'parameterType', 'float')
        self.parameter_type_combo.setCurrentText(parameter_type)
        
        is_exogenous = getattr(self.parameter, 'isExogenous', False)
        self.exogenous_checkbox.setChecked(is_exogenous)

    def _initialize_new_parameter_data(self):
        """Initialize data for new parameter creation."""
        new_id = self._generate_parameter_id()
        self.id_edit.setText(new_id)
        self.name_edit.setText("")
        self.description_edit.setPlainText("")
        self.comment_edit.setPlainText("")
        self.unit_edit.setText("")
        self.value_edit.setText("")
        self.parameter_type_combo.setCurrentText("float")
        self.exogenous_checkbox.setChecked(False)

    def _save_initial_values(self):
        """Save initial values for Undo/Redo commands."""
        self.old_values = {
            "id": self.id_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "comment": self.comment_edit.toPlainText().strip(),
            "unit": self.unit_edit.text().strip(),
            "value": self.value_edit.text().strip(),
            "parameterType": self.parameter_type_combo.currentText(),
            "isExogenous": self.exogenous_checkbox.isChecked()
        }

    # --- Validation and Acceptance Methods ---

    def _validate_data(self) -> bool:
        """
        Perform all data validation.
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        return self._validate_name()

    def _validate_name(self) -> bool:
        """Validate the name field."""
        if not self.name_edit.text().strip():
            QMessageBox.critical(self, "Erreur de validation", "Le Nom (*) ne peut pas être vide.")
            self.name_edit.setFocus()
            return False
        return True

    def get_data(self) -> dict:
        """
        Collect all form data.
        
        Returns:
            dict: All collected form data
        """
        return {
            "id": self.id_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "comment": self.comment_edit.toPlainText().strip(),
            "unit": self.unit_edit.text().strip(),
            "value": self.value_edit.text().strip(),
            "parameterType": self.parameter_type_combo.currentText(),
            "isExogenous": self.exogenous_checkbox.isChecked()
        }

    def accept(self):
        """Handle dialog acceptance with validation and command execution."""
        if not self._validate_data():
            return
            
        new_values = self.get_data()

        if self.parameter is None:
            self._handle_parameter_creation(new_values)
        else:
            self._handle_parameter_edition(new_values)

    def _handle_parameter_creation(self, new_values: dict):
        """Handle parameter creation logic."""
        try:
            self.parameter = self.parent().model_manager.create_parameter(new_values)
            if self.parameter is None:
                raise ValueError("Échec de la création du Paramètre.")
            
            self._finalize_dialog()
            super().accept()
            
        except Exception as error:
            QMessageBox.critical(
                self, 
                "Erreur", 
                f"Échec de la création du Paramètre : {str(error)}"
            )

    def _handle_parameter_edition(self, new_values: dict):
        """Handle parameter edition logic."""
        self._execute_model_commands(new_values)
        self._finalize_dialog()
        super().accept()

    def _execute_model_commands(self, new_values: dict):
        """
        Create and execute ModifyFieldCommand for modified fields.
        
        Args:
            new_values: New values from the form
        """
        if self.parameter is None or not hasattr(self.parent(), 'execute_command'):
            return

        field_mapping = {
            "name": "name",
            "description": "description", 
            "comment": "comment",
            "unit": "unit",
            "value": "value",
            "parameterType": "parameterType",
            "isExogenous": "isExogenous",
        }

        for ecore_field_name, data_key in field_mapping.items():
            if self._is_field_modified(data_key, new_values):
                command = ModifyFieldCommand(
                    self.parent(), 
                    self.parameter, 
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
        
        return old_value != new_value

    def _finalize_dialog(self):
        """Perform cleanup and notification operations after successful acceptance."""
        if hasattr(self.parent(), 'update_navigation_tree'):
            self.parent().update_navigation_tree()
            
        if hasattr(self.parent(), 'model_manager') and hasattr(self.parent().model_manager, 'save_model'):
            self.parent().model_manager.save_model()