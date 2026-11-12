"""
Dialog for editing or creating Resource elements.
Handles resource-specific attributes with flexible connectivity and visual warnings.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QTextEdit, QMessageBox, QLabel,
    QListWidget, QAbstractItemView, QListWidgetItem, QHBoxLayout, QPushButton,
    QComboBox, QGroupBox
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


class ResourceDialog(QDialog):
    """
    Dialog for editing or creating Resource elements.
    
    This dialog provides flexible connectivity with visual warnings for
    missing required references, rather than blocking validation.
    
    According to the metamodel, Resource has a required 'heldBy' reference
    with lowerBound=1, but we allow creation with warnings.
    """

    def __init__(
        self, 
        resource: EObject = None, 
        parent=None, 
        existing_ids=None, 
        current_agents=None,
        connected_entities=None
    ):
        """
        Initialize the ResourceDialog.
        
        Args:
            resource: Existing resource object to edit, or None for creation
            parent: Parent widget
            existing_ids: List of existing resource IDs for uniqueness validation
            current_agents: List of available agents for heldBy reference
            connected_entities: Dictionary of pre-connected entities
        """
        super().__init__(parent)
        
        self.resource = resource
        self.old_values = {}
        self.existing_ids = existing_ids or []
        self.current_agents = current_agents or []
        self.connected_entities = connected_entities or {
            'heldBy': None
        }
        
        self._setup_dialog_configuration()
        self._init_ui()
        self._load_data()
        self._save_initial_values()
        self._update_visual_warnings()

    def _setup_dialog_configuration(self):
        """Configure basic dialog settings."""
        self.setWindowTitle("Éditer Ressource" if self.resource else "Nouvelle Ressource")
        self.resize(450, 550)

    def _init_ui(self):
        """Initialize the main user interface."""
        main_layout = QVBoxLayout(self)
        
        self._add_info_label(main_layout)
        self._setup_form_group(main_layout)
        self._setup_agent_reference_ui(main_layout)
        self._setup_visual_warnings_section(main_layout)
        self._setup_button_box(main_layout)

    def _add_info_label(self, main_layout: QVBoxLayout):
        """Add informational label about flexible connectivity approach."""
        info_label = QLabel(
            "💡 L'éditeur est flexible : vous pouvez créer des ressources même si l'agent "
            "détenteur n'est pas encore connecté. Les éléments manquants seront signalés visuellement."
        )
        info_label.setStyleSheet("color: #2E86AB; background-color: #F0F8FF; padding: 8px; border-radius: 4px;")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

    def _setup_form_group(self, main_layout: QVBoxLayout):
        """Setup the basic information form group."""
        form_group = QGroupBox("Informations de base")
        form_layout = QFormLayout(form_group)
        
        self._setup_id_field(form_layout)
        self._setup_name_field(form_layout)
        self._setup_unit_field(form_layout)
        self._setup_quantity_field(form_layout)
        self._setup_renewable_field(form_layout)
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
        self.name_edit.setPlaceholderText("Nom de la ressource *")
        form_layout.addRow(QLabel("Nom *:"), self.name_edit)

    def _setup_unit_field(self, form_layout: QFormLayout):
        """Setup the unit field."""
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("Unité (ex: kg, m², L)")
        form_layout.addRow(QLabel("Unité:"), self.unit_edit)

    def _setup_quantity_field(self, form_layout: QFormLayout):
        """Setup the quantity field (float)."""
        self.quantity_edit = QLineEdit()
        self.quantity_edit.setPlaceholderText("Quantité (ex: 100.5)")
        form_layout.addRow(QLabel("Quantité:"), self.quantity_edit)

    def _setup_renewable_field(self, form_layout: QFormLayout):
        """Setup the renewable flag combo box."""
        self.renewable_combo = QComboBox()
        self.renewable_combo.addItems(["Oui", "Non"])
        form_layout.addRow(QLabel("Ressource renouvelable:"), self.renewable_combo)

    def _setup_description_field(self, form_layout: QFormLayout):
        """Setup the description text edit."""
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Description détaillée de la ressource")
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow(QLabel("Description:"), self.description_edit)

    def _setup_comment_field(self, form_layout: QFormLayout):
        """Setup the comment text edit."""
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Notes et commentaires")
        self.comment_edit.setMaximumHeight(80)
        form_layout.addRow(QLabel("Commentaire:"), self.comment_edit)

    def _setup_agent_reference_ui(self, main_layout: QVBoxLayout):
        """Setup the agent reference section (heldBy) with connection-based approach."""
        agent_group = QGroupBox("Agent Détenteur (Connexion Requise)")
        agent_layout = QVBoxLayout(agent_group)
        
        # Agent display (read-only, based on connections)
        agent_display_layout = QHBoxLayout()
        agent_display_layout.addWidget(QLabel("Agent détenteur *:"))
        
        self.agent_display = QLineEdit()
        self.agent_display.setReadOnly(True)
        self.agent_display.setPlaceholderText("Aucun agent détenteur connecté")
        agent_display_layout.addWidget(self.agent_display)
        
        self.agent_status = QLabel("❌")
        self.agent_status.setToolTip("Agent détenteur non connecté")
        agent_display_layout.addWidget(self.agent_status)
        
        agent_layout.addLayout(agent_display_layout)
        
        # Information about connectivity
        info_label = QLabel(
            "💡 <b>Connexion requise :</b><br>"
            "Chaque ressource doit être détenue par un agent.<br>"
            "La connexion se fait via l'éditeur graphique en reliant la ressource à un agent."
        )
        info_label.setStyleSheet("color: #666; font-size: 10px; background-color: #FFF9E6; padding: 8px; border-radius: 4px;")
        info_label.setWordWrap(True)
        agent_layout.addWidget(info_label)
        
        # Available agents information (read-only)
        available_agents_layout = QHBoxLayout()
        available_agents_layout.addWidget(QLabel("Agents disponibles:"))
        self.available_agents_label = QLabel("0 agent(s) disponible(s)")
        self.available_agents_label.setStyleSheet("color: gray;")
        available_agents_layout.addWidget(self.available_agents_label)
        available_agents_layout.addStretch()
        agent_layout.addLayout(available_agents_layout)
        
        self.available_agents_display = QTextEdit()
        self.available_agents_display.setReadOnly(True)
        self.available_agents_display.setMaximumHeight(80)
        self.available_agents_display.setPlaceholderText("Aucun agent disponible dans le modèle")
        agent_layout.addWidget(self.available_agents_display)
        
        main_layout.addWidget(agent_group)

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

    def _update_visual_warnings(self):
        """Update visual warnings based on current connectivity state."""
        warnings = []
        
        # Check heldBy agent (required reference)
        held_by_agent = self.connected_entities.get('heldBy')
        if held_by_agent:
            self.agent_display.setText(f"{getattr(held_by_agent, 'name', 'Inconnu')} ({getattr(held_by_agent, 'id', 'ID')})")
            self.agent_display.setStyleSheet("background-color: #E6FFE6; color: #000;")
            self.agent_status.setText("✅")
            self.agent_status.setToolTip("Agent détenteur correctement connecté")
        else:
            self.agent_display.setText("")
            self.agent_display.setStyleSheet("background-color: #FFE6E6; color: #666;")
            self.agent_status.setText("❌")
            self.agent_status.setToolTip("Agent détenteur non connecté")
            warnings.append("• Aucun agent détenteur connecté")
        
        # Update available agents display
        self._update_available_agents_display()
        
        # Update warnings display
        if warnings:
            self.conformity_label.setText("⚠️ Connexion requise manquante")
            self.conformity_label.setStyleSheet("color: #E67E22; font-weight: bold; padding: 8px; background-color: #FFF9E6;")
            self.warnings_list.setText("\n".join(warnings))
            self.warnings_group.setStyleSheet("QGroupBox { border: 2px solid #E67E22; }")
        else:
            self.conformity_label.setText("✅ Toutes les connexions requises sont établies")
            self.conformity_label.setStyleSheet("color: #27AE60; font-weight: bold; padding: 8px; background-color: #E6FFE6;")
            self.warnings_list.setText("")
            self.warnings_group.setStyleSheet("QGroupBox { border: 2px solid #27AE60; }")

    def _update_available_agents_display(self):
        """Update the available agents display."""
        if self.current_agents:
            agents_text = "\n".join([
                f"• {getattr(agent, 'name', 'Inconnu')} ({getattr(agent, 'id', 'ID')})"
                for agent in self.current_agents
            ])
            self.available_agents_display.setPlainText(agents_text)
            self.available_agents_label.setText(f"{len(self.current_agents)} agent(s) disponible(s)")
            self.available_agents_label.setStyleSheet("color: #27AE60; font-weight: bold;")
        else:
            self.available_agents_display.setPlainText("")
            self.available_agents_label.setText("0 agent(s) disponible(s)")
            self.available_agents_label.setStyleSheet("color: #E74C3C; font-weight: bold;")

    # --- Data Handling Methods ---

    def _generate_resource_id(self) -> str:
        """
        Generate a unique resource ID in format 'resource_XXX'.
        
        Returns:
            str: Unique resource ID
        """
        base_id = "resource_"
        counter = 1
        while f"{base_id}{counter:03d}" in self.existing_ids:
            counter += 1
        return f"{base_id}{counter:03d}"

    def _load_data(self):
        """Load data from resource object or initialize with default values."""
        if self.resource:
            self._load_existing_resource_data()
        else:
            self._initialize_new_resource_data()
        
        self._update_visual_warnings()

    def _load_existing_resource_data(self):
        """Load data from existing resource for editing."""
        # Basic fields from NamedElement
        self.id_edit.setText(getattr(self.resource, 'id', ''))
        self.name_edit.setText(getattr(self.resource, 'name', ''))
        self.description_edit.setPlainText(getattr(self.resource, 'description', ''))
        self.comment_edit.setPlainText(getattr(self.resource, 'comment', ''))
        
        # Resource-specific fields
        self.unit_edit.setText(getattr(self.resource, 'unit', ''))
        
        quantity = getattr(self.resource, 'quantity', 0.0)
        self.quantity_edit.setText(str(quantity) if quantity is not None else "")
        
        is_renewable = getattr(self.resource, 'isRenewable', False)
        self.renewable_combo.setCurrentText("Oui" if is_renewable else "Non")

    def _initialize_new_resource_data(self):
        """Initialize data for new resource creation."""
        new_id = self._generate_resource_id()
        self.id_edit.setText(new_id)
        self.name_edit.setText("")
        self.description_edit.setPlainText("")
        self.comment_edit.setPlainText("")
        self.unit_edit.setText("")
        self.quantity_edit.setText("")
        self.renewable_combo.setCurrentText("Non")

    def _save_initial_values(self):
        """Save initial values for Undo/Redo commands."""
        held_by_agent = self.connected_entities.get('heldBy')
        held_by_id = getattr(held_by_agent, 'id', None) if held_by_agent else None
        
        quantity_text = self.quantity_edit.text().strip()
        quantity = float(quantity_text) if quantity_text else 0.0
        
        self.old_values = {
            "id": self.id_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "comment": self.comment_edit.toPlainText().strip(),
            "unit": self.unit_edit.text().strip(),
            "quantity": quantity,
            "isRenewable": self.renewable_combo.currentText() == "Oui",
            "heldBy": held_by_id
        }

    # --- Validation and Acceptance Methods ---

    def _validate_data(self) -> bool:
        """
        Perform flexible validation - warn but don't block.
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        if not self._validate_name():
            return False
            
        if not self._validate_quantity():
            return False
        
        # Show warning for missing required connection but don't block
        held_by_agent = self.connected_entities.get('heldBy')
        
        if not held_by_agent:
            reply = QMessageBox.warning(
                self,
                "Connexion Requise Manquante",
                "Cette ressource nécessite une connexion à un agent détenteur.\n\n"
                "Souhaitez-vous quand même sauvegarder ?\n"
                "Vous pourrez établir la connexion plus tard via l'éditeur graphique.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return reply == QMessageBox.Yes
        
        return True

    def _validate_name(self) -> bool:
        """Validate the name field."""
        if not self.name_edit.text().strip():
            QMessageBox.critical(self, "Erreur de validation", "Le Nom (*) ne peut pas être vide.")
            self.name_edit.setFocus()
            return False
        return True

    def _validate_quantity(self) -> bool:
        """Validate the quantity field (must be a valid float if provided)."""
        quantity_text = self.quantity_edit.text().strip()
        if quantity_text:  # Quantity is optional, but if provided must be valid
            try:
                float(quantity_text)
            except ValueError:
                QMessageBox.critical(
                    self, 
                    "Erreur de validation", 
                    "La quantité doit être un nombre valide (ex: 100.5)."
                )
                self.quantity_edit.setFocus()
                return False
        return True

    def get_data(self) -> dict:
        """
        Collect all form data including references.
        
        Returns:
            dict: All collected form data
        """
        quantity_text = self.quantity_edit.text().strip()
        quantity = float(quantity_text) if quantity_text else 0.0
        
        # heldBy comes from connections, not from UI selection
        held_by_agent = self.connected_entities.get('heldBy')
        
        return {
            "id": self.id_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "comment": self.comment_edit.toPlainText().strip(),
            "unit": self.unit_edit.text().strip(),
            "quantity": quantity,
            "isRenewable": self.renewable_combo.currentText() == "Oui",
            "heldBy": held_by_agent
        }

    def accept(self):
        """Handle dialog acceptance with flexible validation."""
        if not self._validate_data():
            return
            
        new_values = self.get_data()

        if self.resource is None:
            self._handle_resource_creation(new_values)
        else:
            self._handle_resource_edition(new_values)

    def _handle_resource_creation(self, new_values: dict):
        """Handle resource creation logic."""
        try:
            self.resource = self.parent().model_manager.create_resource(new_values)
            if self.resource is None:
                raise ValueError("Échec de la création de la Ressource.")
            
            self._finalize_dialog()
            super().accept()
            
        except Exception as error:
            QMessageBox.critical(
                self, 
                "Erreur", 
                f"Échec de la création de la Ressource : {str(error)}"
            )

    def _handle_resource_edition(self, new_values: dict):
        """Handle resource edition logic."""
        self._execute_model_commands(new_values)
        self._finalize_dialog()
        super().accept()

    def _execute_model_commands(self, new_values: dict):
        """
        Create and execute ModifyFieldCommand for modified fields.
        
        Args:
            new_values: New values from the form
        """
        if self.resource is None or not hasattr(self.parent(), 'execute_command'):
            return

        field_mapping = {
            "name": "name",
            "description": "description", 
            "comment": "comment",
            "unit": "unit",
            "quantity": "quantity",
            "isRenewable": "isRenewable",
            "heldBy": "heldBy",
        }

        for ecore_field_name, data_key in field_mapping.items():
            if self._is_field_modified(data_key, new_values):
                command = ModifyFieldCommand(
                    self.parent(), 
                    self.resource, 
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
        
        if data_key == "heldBy":
            # For agent reference, compare IDs
            old_agent_id = old_value
            new_agent_id = getattr(new_value, 'id', None) if new_value else None
            return old_agent_id != new_agent_id
        elif data_key == "quantity":
            # For quantity, compare float values
            old_quantity = float(old_value) if old_value else 0.0
            new_quantity = new_value if new_value is not None else 0.0
            return abs(old_quantity - new_quantity) > 0.0001
        else:
            # For other fields, direct comparison
            return old_value != new_value

    def _finalize_dialog(self):
        """Perform cleanup and notification operations after successful acceptance."""
        if hasattr(self.parent(), 'update_navigation_tree'):
            self.parent().update_navigation_tree()
            
        if hasattr(self.parent(), 'model_manager') and hasattr(self.parent().model_manager, 'save_model'):
            self.parent().model_manager.save_model()