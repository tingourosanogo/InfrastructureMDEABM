# ui/setup_wizard.py
from PySide6.QtWidgets import (
    QApplication, QProgressDialog, QSizePolicy, QWizard, QWizardPage, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QCheckBox, QGroupBox, QFileDialog, QMessageBox,
    QProgressBar, QTextEdit, QScrollArea, QFrame, QWidget
)
from PySide6.QtCore import QProcess, Qt, QTimer, QProcessEnvironment
from PySide6.QtGui import QFont, QIcon, QPixmap, QImage
from pathlib import Path
import json
import subprocess
import sys, os
import io


# ====================== PAGES ======================

class IntroPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Générateur de Modèles GAML")
        self.setSubTitle("Propulsez vos modèles conceptuels vers la simulation GAMA.")

        layout = QVBoxLayout()
        layout.setSpacing(25)

        # --- 1. Modern Hero Banner ---
        self.hero_label = QLabel(
            "Automatisez la transition entre vos diagrammes XMI et votre code de simulation. "
            "Gérez vos ressources et vos paramètres d'instanciation en quelques clics."
        )
        self.hero_label.setWordWrap(True)
        self.hero_label.setStyleSheet("""
            font-size: 13px; 
            color: #57606f; 
            line-height: 150%;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin: 10px 0;
        """)
        layout.addWidget(self.hero_label)

        # --- 2. Transformation Container (Pivot UI) ---
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #f1f2f6;
                border: 1px solid #dcdde1;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(container)
        
        demo_title = QLabel("APERÇU DE LA COMPILATION GAML")
        demo_title.setStyleSheet("""
            font-weight: bold; color: #2f3542; font-size: 10px; 
            letter-spacing: 1px; border: none; padding-bottom: 5px;
        """)
        container_layout.addWidget(demo_title)

        example_layout = QHBoxLayout()
        example_layout.setSpacing(0)

        # Left Editor (Source / Deep Charcoal)
        self.pseudo_code = QTextEdit()
        self.pseudo_code.setPlainText(
            "// Pseudo-code\n"
            "soil_temp = soil_temperature;\n"
            "temp_factor = exp(0.069 * (soil_temp - 10));\n"
            "if (temp_factor < 0) {\n"
            "    temp_factor = 0;\n"
            "}"
        )
        self.pseudo_code.setReadOnly(True)
        self.pseudo_code.setMinimumHeight(150)
        self.pseudo_code.setStyleSheet("""
            QTextEdit {
                background-color: #2d3436;      /* Pivot Deep Charcoal */
                color: #fab1a0;                 /* Pivot Coral */
                font-family: 'Consolas', monospace;
                font-size: 10px;
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
                padding: 12px;
                border: 1px solid #1e272e;
            }
        """)

        # Arrow Link
        arrow_container = QWidget()
        arrow_container.setStyleSheet("background-color: #f1f2f6; border: none;")
        arrow_layout = QVBoxLayout(arrow_container)
        arrow = QLabel("→")
        arrow.setStyleSheet("font-size: 28px; color: #74b9ff; font-weight: bold; border: none;")
        arrow_layout.addWidget(arrow, 0, Qt.AlignCenter)

        # Right Editor (Output / Steel Grey)
        self.gaml_code = QTextEdit()
        self.gaml_code.setPlainText(
            "// Code GAML Généré\n"
            "soil_temp <- soil_temperature;\n"
            "temp_factor <- exp(0.069 * (soil_temp - 10));\n"
            "if (temp_factor < 0) {\n"
            "    temp_factor <- 0;\n"
            "}"
        )
        self.gaml_code.setReadOnly(True)
        self.gaml_code.setMinimumHeight(150)
        self.gaml_code.setStyleSheet("""
            QTextEdit {
                background-color: #636e72;      /* Pivot Steel Grey */
                color: #ffffff;                 /* Pure White */
                font-family: 'Consolas', monospace;
                font-size: 10px;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                padding: 12px;
                border: 1px solid #2f3542;
                border-left: none;
            }
        """)

        example_layout.addWidget(self.pseudo_code, 2)
        example_layout.addWidget(arrow_container, 1)
        example_layout.addWidget(self.gaml_code, 2)
        
        container_layout.addLayout(example_layout)
        layout.addWidget(container)

        # --- 3. Feature Badge ---
        self.footer_info = QLabel("✨ Support natif : GAML 1.9+, Modèles GAMA 2024.")
        self.footer_info.setStyleSheet("""
            color: #57606f; font-size: 11px; font-weight: 600;
            background-color: #e1e4e8; padding: 5px 12px; border-radius: 15px;
        """)
        layout.addWidget(self.footer_info)

        layout.addStretch()
        self.setLayout(layout)


class XmiPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Modèle Conceptuel")
        self.setSubTitle("Définissez la structure source de votre simulation (XMI).")

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # --- 1. Card Container (Pivot UI) ---
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame { 
                    background-color: transparent; 
                    border: 1px solid #dcdde1; 
                    border-radius: 10px;
                    padding: 5px;
                }
            QLabel { border: none; font-weight: bold; color: #34495e; }
        """)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(12)

        title_label = QLabel("📂 Fichier Source XMI :")
        title_label.setStyleSheet("font-weight: bold; color: #3498db; font-size: 13px;")
        title_label.setCursor(Qt.WhatsThisCursor)

        card_layout.addWidget(title_label)

        # --- 2. Input Row (Edit + Status + Browse) ---
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Sélectionnez le fichier .xmi...")
        self.path_edit.setMinimumHeight(35)
        self.path_edit.setToolTip("Entrez ou parcourez pour sélectionner le fichier de modèle XMI source.")
        
        # Dynamic Status Icon
        self.status_icon = QLabel(" ⚪ ")
        self.status_icon.setFixedWidth(30)
        self.status_icon.setAlignment(Qt.AlignCenter)
        self.status_icon.setToolTip("Vérification de l'accessibilité des fichiers...")

        self.browse_btn = QPushButton("Parcourir...")
        self.browse_btn.setMinimumWidth(110)
        self.browse_btn.setToolTip("Ouvrir l'explorateur de fichiers pour choisir un fichier .xmi")
        
        input_layout.addWidget(self.path_edit, 1)
        input_layout.addWidget(self.status_icon)
        input_layout.addWidget(self.browse_btn)
        
        card_layout.addLayout(input_layout)

        # --- 3. Dynamic Help Tip ---
        self.help_tip = QLabel("💡  Astuce : Exportez votre modèle au format XMI pour une meilleure compatibilité.")
        self.help_tip.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic; border: none;")
        card_layout.addWidget(self.help_tip)

        layout.addWidget(self.card)
        layout.addStretch()
        self.setLayout(layout)

        # --- Connections & Fields ---
        self.registerField("xmi_path*", self.path_edit) 
        self.path_edit.textChanged.connect(self.validate_xmi)
        self.browse_btn.clicked.connect(self.browse_xmi)

    def browse_xmi(self):
        """Standard File Picker with strict Filter"""
        file, _ = QFileDialog.getOpenFileName(
            self, 
            "Sélectionner le modèle XMI", 
            "", 
            "Modèles XMI (*.xmi);;Tous les fichiers (*)"
        )
        if file:
            self.path_edit.setText(file)

    def validate_xmi(self):
        """Dynamic Non-Intrusive Validation"""
        path = self.path_edit.text().strip()
        p = Path(path)

        if not path:
            self.status_icon.setText("⚪")
            self.status_icon.setToolTip("Aucun fichier sélectionné.")
        elif p.exists() and p.is_file() and p.suffix.lower() == ".xmi":
            self.status_icon.setText("✅")
            self.status_icon.setToolTip(f"Fichier valide trouvé ({p.name})")
        else:
            self.status_icon.setText("❌")
            self.status_icon.setToolTip("Erreur : Le fichier doit être un .xmi existant.")
        
        # Notify the Wizard to re-check the 'Next' button state
        self.completeChanged.emit()

    def isComplete(self):
        """The 'Next' button only enables if the path is truly valid"""
        path = self.path_edit.text().strip()
        p = Path(path)
        return bool(path) and p.exists() and p.suffix.lower() == ".xmi"


class InputPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Données d'Instanciation")
        self.setSubTitle("Sélectionnez le dossier contenant vos fichiers de ressources et paramètres.")

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # --- 1. Card Container (Pivot UI) ---
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame { 
                background-color: transparent; 
                border: 1px solid #dcdde1; 
                border-radius: 10px;
                padding: 5px;
            }
            QLabel { border: none; font-weight: bold; color: #34495e; }
        """)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(12)

        title_label = QLabel("📂 Dossier de Configuration :")
        title_label.setStyleSheet("font-weight: bold; color: #3498db; font-size: 13px;")
        
        card_layout.addWidget(title_label)

        # --- 2. Input Row (Edit + Status + Browse) ---
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Sélectionnez le dossier racine...")
        self.path_edit.setMinimumHeight(35)
        self.path_edit.setToolTip("Dossier contenant les fichiers de données (YAML, JSON, CSV).")
        
        # Dynamic Status Icon
        self.status_icon = QLabel(" ⚪ ")
        self.status_icon.setFixedWidth(30)
        self.status_icon.setAlignment(Qt.AlignCenter)
        self.status_icon.setToolTip("Analyse du contenu du dossier...")

        self.browse_btn = QPushButton("Parcourir...")
        self.browse_btn.setMinimumWidth(110)
        self.browse_btn.setToolTip("Choisir le dossier de configuration via l'explorateur")
        
        input_layout.addWidget(self.path_edit, 1)
        input_layout.addWidget(self.status_icon)
        input_layout.addWidget(self.browse_btn)
        
        card_layout.addLayout(input_layout)

        # --- 3. Dynamic Help Tip ---
        self.help_tip = QLabel("💡  Info : Le dossier doit contenir au moins un fichier .json, .yml ou .csv.")
        self.help_tip.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic; border: none;")
        card_layout.addWidget(self.help_tip)

        layout.addWidget(self.card)
        layout.addStretch()
        self.setLayout(layout)

        # --- Connections & Fields ---
        # Registering with * handles the button state but we keep isComplete for depth
        self.registerField("input_dir*", self.path_edit) 
        self.path_edit.textChanged.connect(self.validate_input_dir)
        self.browse_btn.clicked.connect(self.browse_dir)

    def browse_dir(self):
        """Folder selection dialog"""
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de configuration")
        if dir_path:
            self.path_edit.setText(dir_path)

    def validate_input_dir(self):
        """Dynamic background validation (No popups)"""
        path = self.path_edit.text().strip()
        p = Path(path)

        if not path:
            self.status_icon.setText("⚪")
            self.status_icon.setToolTip("Aucun dossier sélectionné.")
            return

        if p.exists() and p.is_dir():
            # Scan for supported files
            files = list(p.glob("*.json")) + list(p.glob("*.yml")) + \
                    list(p.glob("*.yaml")) + list(p.glob("*.csv"))
            
            if files:
                self.status_icon.setText("✅")
                self.status_icon.setToolTip(f"{len(files)} fichiers de config trouvés.")
            else:
                self.status_icon.setText("⚠️")
                self.status_icon.setToolTip("Le dossier existe mais ne contient aucun fichier supporté (.json, .yml, .csv).")
        else:
            self.status_icon.setText("❌")
            self.status_icon.setToolTip("Erreur : Le dossier spécifié n'existe pas.")
        
        # Trigger Wizard button re-check
        self.completeChanged.emit()

    def isComplete(self):
        """Strict validation: Folder must exist and contain at least 1 file"""
        path = self.path_edit.text().strip()
        p = Path(path)
        if not path or not p.exists() or not p.is_dir():
            return False
        
        # Simple check for file presence
        extensions = ['*.json', '*.yml', '*.yaml', '*.csv']
        return any(any(p.glob(ext)) for ext in extensions)


class OutputPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Destination du Code GAML")
        self.setSubTitle("Définissez l'emplacement où les fichiers générés seront sauvegardés.")

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # --- 1. Card Container (Pivot UI) ---
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame { 
                background-color: transparent; 
                border: 1px solid #dcdde1; 
                border-radius: 10px;
                padding: 5px;
            }
            QLabel { border: none; font-weight: bold; color: #34495e; }
        """)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(12)

        title_label = QLabel("📁 Dossier de Sortie :")
        title_label.setStyleSheet("font-weight: bold; color: #3498db; font-size: 13px;")
        card_layout.addWidget(title_label)

        # --- 2. Input Row (Edit + Status + Browse) ---
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Sélectionnez le dossier de destination...")
        self.path_edit.setMinimumHeight(35)
        self.path_edit.setToolTip("Emplacement final des fichiers .gaml générés.")
        
        # Dynamic Status Icon
        self.status_icon = QLabel(" ⚪ ")
        self.status_icon.setFixedWidth(30)
        self.status_icon.setAlignment(Qt.AlignCenter)
        self.status_icon.setToolTip("Vérification des droits d'écriture...")

        self.browse_btn = QPushButton("Parcourir...")
        self.browse_btn.setMinimumWidth(110)
        self.browse_btn.setToolTip("Choisir le dossier de sortie via l'explorateur")
        
        input_layout.addWidget(self.path_edit, 1)
        input_layout.addWidget(self.status_icon)
        input_layout.addWidget(self.browse_btn)
        
        card_layout.addLayout(input_layout)

        # --- 3. Dynamic Help Tip ---
        self.help_tip = QLabel("💡  Conseil : Choisissez un dossier vide pour éviter toute confusion avec d'anciens modèles.")
        self.help_tip.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic; border: none;")
        card_layout.addWidget(self.help_tip)

        layout.addWidget(self.card)
        layout.addStretch()
        self.setLayout(layout)

        # --- Connections & Fields ---
        self.registerField("output_dir*", self.path_edit) 
        self.path_edit.textChanged.connect(self.validate_output_dir)
        self.browse_btn.clicked.connect(self.browse_output_dir)

    def browse_output_dir(self):
        """Standard Folder Picker"""
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de sortie")
        if dir_path:
            self.path_edit.setText(dir_path)

    def validate_output_dir(self):
        """Dynamic Write-Access Validation (Silent)"""
        path = self.path_edit.text().strip()
        p = Path(path)

        if not path:
            self.status_icon.setText("⚪")
            self.status_icon.setToolTip("Aucun dossier sélectionné.")
        elif p.exists() and p.is_dir():
            # Test Writing Permission (Pro-active Check)
            try:
                test_file = p / f".write_test_{os.getpid()}.tmp"
                test_file.touch()
                test_file.unlink()
                self.status_icon.setText("✅")
                self.status_icon.setToolTip("Dossier accessible en écriture.")
            except Exception:
                self.status_icon.setText("❌")
                self.status_icon.setToolTip("ERREUR : Droits d'écriture refusés sur ce dossier.")
        else:
            self.status_icon.setText("❌")
            self.status_icon.setToolTip("ERREUR : Dossier inexistant ou chemin invalide.")
        
        self.completeChanged.emit()

    def isComplete(self):
        """Final check for the Wizard 'Next' button"""
        path = self.path_edit.text().strip()
        p = Path(path)
        if not path or not p.exists() or not p.is_dir():
            return False
        
        # Fast write check without popups
        return os.access(path, os.W_OK)


class OptionsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Options de Configuration GAML")
        self.setSubTitle("Personnalisez la structure et les fonctionnalités du code généré.")

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # --- 1. Conteneur d'Options (Card UI) ---
        self.card = QFrame()
                # --- Conteneur d'Options Stylisé (Version Corrigée) ---
        self.card.setStyleSheet("""
            QFrame { 
                background-color: #f1f2f6; 
                border: 1px solid #dcdde1; 
                border-radius: 10px;
            }
            QCheckBox { 
                font-weight: bold; 
                color: #2f3542; 
                spacing: 12px;
                border: none;
                background: transparent;
                padding: 10px;
            }
            /* On force l'affichage du carré */
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                background-color: white;
            }
            /* Changement de couleur au survol */
            QCheckBox::indicator:hover {
                border-color: #3498db;
            }
            /* État COCHÉ : On utilise une couleur de fond pleine avec un symbole texte 
               C'est la méthode la plus compatible sans fichiers externes */
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
                /* On peut aussi utiliser une image locale si vous en avez une, 
                   sinon le changement de couleur est déjà très explicite */
            }
            
            /* Ajustement des labels de description pour l'alignement */
            QLabel { 
                border: none; 
                color: #57606f; 
                font-size: 11px; 
                margin-left: 45px; /* Augmenté pour s'aligner sous le texte */
                padding-bottom: 5px;
            }
        """)

        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # --- Option 1: Mode Modulaire ---
        self.modular_cb = QCheckBox("Mode Modulaire (Multi-fichiers)")
        self.modular_cb.setToolTip("Sépare le code par espèce pour une meilleure lisibilité.")
        modular_desc = QLabel("Génère un fichier .gaml distinct pour chaque espèce au lieu d'un fichier unique.")
        modular_desc.setWordWrap(True)
        
        # --- Option 2: Réflexes Automatiques ---
        self.reflex_cb = QCheckBox("Générer les Réflexes Automatiquement")
        self.reflex_cb.setChecked(True)
        self.reflex_cb.setToolTip("Incorpore les comportements dynamiques définis dans le modèle.")
        reflex_desc = QLabel("Active la traduction des actions et comportements UML en réflexes GAML.")
        
        # --- Option 3: Diagnostics ---
        self.diag_cb = QCheckBox("Activer les Diagnostics Détaillés")
        self.diag_cb.setChecked(True)
        self.diag_cb.setToolTip("Ajoute des logs de debug pour faciliter le test dans GAMA.")
        diag_desc = QLabel("Ajoute des instructions 'write' dans le code pour tracer l'exécution des agents.")

        # Ajout au layout
        card_layout.addWidget(self.modular_cb)
        card_layout.addWidget(modular_desc)
        
        # Ligne de séparation subtile
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken); line.setStyleSheet("color: #dcdde1;")
        card_layout.addWidget(line)
        
        card_layout.addWidget(self.reflex_cb)
        card_layout.addWidget(reflex_desc)
        
        card_layout.addWidget(self.diag_cb)
        card_layout.addWidget(diag_desc)

        layout.addWidget(self.card)
        layout.addStretch()
        self.setLayout(layout)

        # --- Enregistrement des champs ---
        self.registerField("modular_mode", self.modular_cb)
        self.registerField("generate_reflex", self.reflex_cb)
        self.registerField("include_diagnostics", self.diag_cb)


class SummaryPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Vérification du Plan de Génération")
        self.setSubTitle("Validez les paramètres avant de compiler le modèle GAML.")

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Widget de contenu avec style Dashboard
        self.content_area = QLabel()
        self.content_area.setWordWrap(True)
        self.content_area.setTextFormat(Qt.RichText)
        self.content_area.setStyleSheet("""
            QLabel {
                background-color: #f1f2f6;
                border: 1px solid #dcdde1;
                border-left: 5px solid #3498db;
                border-radius: 8px;
                padding: 20px;
                color: #2f3542;
            }
        """)

        # Bandeau d'astuce contextuel
        self.info_box = QLabel("💡 Astuce : Le mode modulaire est recommandé pour les modèles complexes.")
        self.info_box.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 11px; padding: 5px;")

        layout.addWidget(self.content_area)
        layout.addWidget(self.info_box)
        layout.addStretch()
        self.setLayout(layout)

    def initializePage(self):
        wizard = self.wizard()
        
        # Récupération des données
        xmi = self.field("xmi_path")
        input_dir = self.field("input_dir")
        output_dir = self.field("output_dir")
        mode = "Modulaire" if self.field("modular_mode") else "Monolithique"
        reflex = "Activé" if self.field("generate_reflex") else "Désactivé ❌"
        diag = "Activé" if self.field("include_diagnostics") else "Désactivé ❌"

        html = f"""
        <table width='100%' cellpadding='6' style='margin: 0px;'>
            <tr>
                <td colspan='2' style='font-size: 13px; font-weight: bold; color: #3498db; text-transform: uppercase; letter-spacing: 1px;'>
                    SOURCES & DESTINATION
                </td>
            </tr>
            <tr>
                <td width='40%' style='color: #57606f; font-weight: bold;'>Modèle XMI :</td>
                <td style='font-family: Consolas; color: #2d3436;'>{xmi}</td>
            </tr>
            <tr>
                <td style='color: #57606f; font-weight: bold;'>Dossier Config :</td>
                <td style='font-family: Consolas; font-size: 11px; color: #218c74;'>{input_dir}</td>
            </tr>
            <tr>
                <td style='color: #57606f; font-weight: bold;'>Sortie GAML :</td>
                <td style='font-family: Consolas; font-size: 11px; color: #218c74;'>{output_dir}</td>
            </tr>
            <tr><td colspan='2'><hr style='border: 0; border-top: 1px solid #dcdde1; margin: 10px 0;'></td></tr>
            <tr>
                <td colspan='2' style='font-size: 13px; font-weight: bold; color: #3498db; text-transform: uppercase; letter-spacing: 1px;'>
                    PARAMÈTRES DE COMPILATION
                </td>
            </tr>
            <tr>
                <td style='color: #57606f;'>Structure :</td>
                <td style='font-weight: bold;'>{mode}</td>
            </tr>
            <tr>
                <td style='color: #57606f;'>Réflexes :</td>
                <td style='font-weight: bold;'>{reflex}</td>
            </tr>
            <tr>
                <td style='color: #57606f;'>Diagnostics :</td>
                <td style='font-weight: bold;'>{diag}</td>
            </tr>
        </table>
        """
        self.content_area.setText(html)


class LogPage(QWizardPage):
    def __init__(self, log_widget, parent=None):
        super().__init__(parent)
        self.setTitle("Console d'Exécution GAML")
        self.setSubTitle("Suivez la compilation et la génération des fichiers GAML en temps réel.")
        
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 1. Console Frame
        self.console_frame = QGroupBox("Terminal de sortie")
        self.console_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold; text-transform: uppercase; color: #3498db;
                border: 2px solid #dcdde1; border-radius: 8px; margin-top: 12px; padding-top: 10px;
            }
        """)
        
        frame_layout = QVBoxLayout()
        # We reuse the global log_widget initialized in the Wizard
        frame_layout.addWidget(log_widget)
        self.console_frame.setLayout(frame_layout)
        
        # 2. Modern Status Bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("INITIALISATION...")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #1e272e; color: #2ecc71;
                font-weight: bold; padding: 8px 15px; border-radius: 4px;
                border-left: 4px solid #2ecc71;
            }
        """)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addWidget(self.console_frame)
        layout.addLayout(status_layout)
        self.setLayout(layout)

    def set_status(self, text, color="#2ecc71"):
        """Updates the status bar color and text dynamically"""
        self.status_label.setText(text.upper())
        self.status_label.setStyleSheet(f"""
            background-color: #1e272e; color: {color};
            font-weight: bold; padding: 8px 15px; border-radius: 4px;
            border-left: 4px solid {color};
        """)

    def isComplete(self):
        # Le bouton "Terminer" ne s'active que si le processus est fini
        return getattr(self.wizard(), 'generation_finished', False)

    def validatePage(self):
        # Empêche le retour en arrière si la génération est en cours
        return getattr(self.wizard(), 'generation_finished', False)


# ========================== Classe principale ==========================

class SetupWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Générateur GAML - Assistant de configuration")
        self.setWizardStyle(QWizard.ModernStyle)

        # Ajout de l'icône d'application
        self.setWindowIcon(self.load_app_icon())

        # Options du wizard
        self.setOption(QWizard.NoBackButtonOnStartPage, True)      # Back cliquable dès la première page
        self.setOption(QWizard.DisabledBackButtonOnLastPage, False) # Back cliquable sur la dernière page
        self.setOption(QWizard.IndependentPages, True)              # Navigation totalement libre (Back/Next toujours actifs)
        self.setOption(QWizard.HaveHelpButton, False)          # Pas de bouton d'aide (on peut le réactiver si besoin)
        #self.setOption(QWizard.HaveFinishButtonOnEarlyPages, True) # Finish cliquable dès que les champs sont valides, même avant la dernière page
        

        # Active les boutons classiques de fenêtre (Réduire / Agrandir / Fermer)
        self.setWindowFlags(
            Qt.Window | 
            Qt.CustomizeWindowHint |        # Permet de personnaliser les boutons
            Qt.WindowTitleHint |            # Affiche le titre de la fenêtre
            Qt.WindowSystemMenuHint |       # Affiche le menu système (clic droit sur la barre de titre)
            Qt.WindowMinimizeButtonHint |   # Affiche le bouton de réduction
            Qt.WindowMaximizeButtonHint |   # Affiche le bouton d'agrandissement
            Qt.WindowCloseButtonHint        # Affiche le bouton de fermeture
        )

        self.setSizeGripEnabled(True)           # Active le grip de redimensionnement
        self.setWindowState(Qt.WindowNoState)   # Réinitialise l'état de la fenêtre pour éviter les problèmes de redimensionnement sur certains systèmes

        # Tailles et position
        self.resize(850, 720) 
        self.setMinimumSize(800, 680)
        self.center_on_screen()

        
        # === Ajout des pages ===
        # 1. Créer la console 
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setPlaceholderText("Les logs de génération s'afficheront ici...")
        self.log_console.setUndoRedoEnabled(False) # Gain de performance pour les longs logs
        self.log_console.setLineWrapMode(QTextEdit.NoWrap) # Optionnel : évite le retour à la ligne automatique
        # Style sombre type terminal
        self.log_console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; 
                color: #dcdcdc; 
                font-family: 'Consolas', 'Monaco', monospace;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        self.log_console.setMinimumHeight(120)

        # 2. Créer les pages
        self.intro_page = IntroPage()
        self.xmi_page = XmiPage()
        self.input_page = InputPage()
        self.output_page = OutputPage()
        self.options_page = OptionsPage()
        self.summary_page = SummaryPage()
        self.log_page = LogPage(self.log_console)

        # 3. Ajouter les pages au Wizard
        self.addPage(self.intro_page)
        self.addPage(self.xmi_page)
        self.addPage(self.input_page)
        self.addPage(self.output_page)
        self.addPage(self.options_page)
        self.addPage(self.summary_page)
        self.addPage(self.log_page)

        # Traduction des boutons en français
        self.setButtonText(QWizard.BackButton, "Précédent")
        self.setButtonText(QWizard.NextButton, "Suivant")
        self.setButtonText(QWizard.CommitButton, "Suivant")
        self.setButtonText(QWizard.FinishButton, "Terminer")
        self.setButtonText(QWizard.CancelButton, "Annuler")

        # Connexions
        self.currentIdChanged.connect(self._handle_ui_updates)
        self.button(QWizard.NextButton).clicked.connect(self._on_next_clicked)

    def _on_next_clicked(self):
        """Unified Router: Déclenche la sauvegarde et la génération sur la SummaryPage"""
        # Dans votre ordre : 0:Intro, 1:Xmi, 2:Input, 3:Output, 4:Options, 5:Summary 6:Log

        if self.currentId() == 5:
            # On lance la sauvegarde et la génération
            self.start_generation()
        else:
            # Sinon on avance normalement
            pass

    def _handle_ui_updates(self, current_id):
        """Met à jour uniquement l'aspect visuel des boutons"""

        # 1. Gestion du texte du bouton principal
        if current_id == 5: # SummaryPage
            self.summary_page.initializePage() # Forcer le rafraîchissement
            self.setButtonText(QWizard.NextButton, "Lancer la génération")
        elif current_id == 6: # LogPage (Si vous l'ajoutez)
            self.setButtonText(QWizard.FinishButton, "Terminer")
        else:
            self.setButtonText(QWizard.NextButton, "Suivant")

        # 2. Gestion de la navigation (Précédent / Annuler)
        back_btn = self.button(QWizard.BackButton)
        cancel_btn = self.button(QWizard.CancelButton)

        # Désactiver le bouton retour seulement sur la page de logs (ID 6)
        if current_id == 6:
            back_btn.setEnabled(False)
            cancel_btn.setVisible(False)
        else:
            back_btn.setEnabled(current_id > 0)
            cancel_btn.setVisible(True)



    def load_app_icon(self) -> QIcon:
        """Charge l'icône de l'application de façon robuste"""
        current_dir = Path(__file__).parent  # dossier ui/
        
        # Essayer plusieurs formats et noms possibles
        possible_icons = [
            current_dir / "gaml_generator.ico",
            current_dir / "gaml_generator.png",        
            current_dir / "icon.png"
        ]

        for icon_path in possible_icons:
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    return icon

        # Fallback : icône par défaut si rien n'est trouvé
        print("⚠️ Aucune icône trouvée → utilisation d'une icône texte par défaut")
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        # Tu peux dessiner un logo simple ici si tu veux
        return QIcon(pixmap)
        

    def center_on_screen(self):
        """Centre la fenêtre sur l'écran principal"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def on_finished(self, result):
        """Lorsque l'utilisateur clique sur 'Finish', sauvegarde la config et lance la génération"""
        if result == QWizard.Accepted:
            self.start_generation()

    def save_config(self):
        """Sauvegarde la configuration dans config_gama.json"""
        config = {
            "metadata": {"title": "Générateur GAML", "version": "1.0.0"},
            "paths": {
                "xmi": {
                    "directory": Path(self.field("xmi_path")).as_posix(),
                    "format": "xmi"
                },
                "input_pseudocode": {
                    "directory": Path(self.field("input_dir")).as_posix(),
                    "format": "auto"
                },
                "output_gaml": {
                    "directory": Path(self.field("output_dir")).as_posix()
                }
            },
            "generation": {
                "mode": "modular" if self.field("modular_mode") else "monolithic",
                "generate_reflex": self.field("generate_reflex"),
                "include_diagnostics": self.field("include_diagnostics")
            }
        }

        try:
            with open("config_gama.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de sauvegarder la configuration :\n{e}")
            return False


    def start_generation(self):
        """Lance main_gama.py de façon robuste avec QProcess"""
         # 1. Sauvegarde
        if not self.save_config():
            return
        
        # 2. Préparation de l'état
        self.generation_finished = False
        self.log_console.clear()
        self.log_console.append("<b style='color: #74b9ff;'>[SYSTEM]</b> Démarrage de l'analyse XMI...")

        # 3. Transition UI
        # On passe à la page suivante (LogPage) AVANT de lancer le processus
        self.next() 
            
        self.setButtonText(QWizard.FinishButton, "Terminer")
        # On le désactive le temps de la génération pour respecter l'UX
        self.button(QWizard.FinishButton).setEnabled(False)
        # On désactive aussi le bouton retour pour éviter de casser le process
        self.button(QWizard.BackButton).setEnabled(False)

            
        try:
            project_root = Path(__file__).resolve().parent.parent   # Racine du projet

            # Création du dialogue de progression
            self.progress_dialog = QProgressDialog("Génération en cours...", "Annuler", 0, 0, self)
            self.progress_dialog.setWindowTitle("Progression")
            self.progress_dialog.setMaximumWidth(600) 
            self.progress_dialog.setWindowModality(Qt.WindowModal)

            self.progress_dialog.canceled.connect(self.cancel_generation)
            self.progress_dialog.show()

            self.process = QProcess(self)
            env = QProcessEnvironment.systemEnvironment()
            env.insert("PYTHONIOENCODING", "UTF-8")
            env.insert("PYTHONUTF8", "1")
            self.process.setProcessEnvironment(env)

            self.process.setWorkingDirectory(str(project_root))
            self.process.setProgram(sys.executable)
            self.process.setArguments(["main_gama.py"])

            # 5. Connections
            self.process.readyReadStandardOutput.connect(self.read_stdout)
            self.process.readyReadStandardError.connect(self.read_stderr)
            self.process.finished.connect(self.on_generation_finished)

            self.process.start()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lancer la génération :\n{str(e)}")

    def read_stdout(self):
        raw = self.process.readAllStandardOutput()
        try:
            output = bytes(raw).decode("utf-8")
        except UnicodeDecodeError:
            try:
                output = bytes(raw).decode("utf-8", errors="replace")
            except:
                #output = bytes(raw).decode("latin-1", errors="replace")
                output = bytes(raw).decode("cp1252")

        if output:
            # 1. Mise à jour barre de progression (Texte brut pour le label)
            #last_line = output.splitlines()[-1]
            #self.progress_dialog.setLabelText(last_line[:80])

            # 2. Console de logs (On utilise append pour le HTML)
            clean_line = output.replace("\n", "<br>")
            # On utilise .append() qui détecte automatiquement le HTML
            self.log_console.append(f"<span style='color: #98c379;'></span> {clean_line}")
            
            # Défilement automatique
            scrollbar = self.log_console.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def read_stderr(self):
        raw = self.process.readAllStandardError()
        try:
            error = bytes(raw).decode("utf-8")
        except UnicodeDecodeError:
            try:
                error = bytes(raw).decode("utf-8", errors="replace")
            except:
                #error = bytes(raw).decode("latin-1", errors="replace")
                error = bytes(raw).decode("cp1252")

        if error:
            # 1. Mise à jour barre de progression
            #last_line = error.splitlines()[-1]
            #self.progress_dialog.setLabelText("MESSAGE : " + last_line[:70])
            
            # 2. Console de logs (Couleur rouge pour les erreurs)
            clean_error = error.replace("\n", "<br>")
            self.log_console.append(f"<span style='color: #e06c75; font-weight: bold;'></span> {clean_error}")
            
            # Défilement automatique
            scrollbar = self.log_console.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())


    def on_generation_finished(self, exit_code, exit_status):
        """Appelée quand le script main_gama.py s'arrête"""
        self.generation_finished = True

        # On ferme la petite barre de progression flottante
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        # Mise à jour du statut sur la LogPage
        if exit_code == 0:
            self.log_page.set_status("Génération réussie", "#2ecc71")
            self.log_console.append("<br><span style='color: #2ecc71;'><b>[SUCCESS]</b> Modèle GAML généré avec succès.</span>")
        else:
            self.log_page.set_status("Échec de génération", "#e06c75")
            self.log_console.append(f"<br><span style='color: #e06c75;'><b>[ERROR]</b> Le processus a échoué (Code {exit_code}).</span>")
        
        # Maintenant que c'est fini, l'utilisateur peut cliquer sur "Terminer"
        btn_finish = self.button(QWizard.FinishButton)
        btn_finish.setEnabled(True)

        # On reconnecte le bouton pour qu'il ferme enfin le Wizard
        btn_finish.clicked.disconnect()
        btn_finish.clicked.connect(self.accept) 

    
    def cancel_generation(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            QMessageBox.information(self, "Annulé", "La génération a été annulée.")
            self.progress_dialog.close()

    # Assure-toi que le processus est correctement arrêté si l'utilisateur ferme la fenêtre pendant la génération
    def closeEvent(self, event):
        if hasattr(self, 'process') and self.process.state() == QProcess.Running:
            self.process.kill()
        event.accept() 