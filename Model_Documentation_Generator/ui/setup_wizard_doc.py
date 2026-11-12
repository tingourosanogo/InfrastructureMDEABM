#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QApplication, QListWidget, QListWidgetItem, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTextEdit, QFileDialog, QGroupBox,
    QFormLayout, QMessageBox, QProgressDialog, QSpacerItem, QSizePolicy, QDialog, QWidget,
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, Signal, QProcess, QProcessEnvironment
from PySide6.QtGui import QPixmap, QIcon, QPalette, QColor


class IntroDocPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Générateur de Documentation")
        self.setSubTitle("Propulsez vos modèles vers des livrables professionnels.")

        layout = QVBoxLayout()
        layout.setSpacing(25)

        # --- 1. Bannière d'accueil stylisée ---
        self.hero_label = QLabel(
            "Transformez vos sources de données (XMI, YAML, CSV) en une documentation "
            "structurée, élégante et prête à l'export."
        )
        self.hero_label.setWordWrap(True)
        self.hero_label.setStyleSheet("""
            font-size: 14px; 
            color: #57606f;
            line-height: 140%;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin: 10px 0;
            background-color: transparent;
        """)
        layout.addWidget(self.hero_label)

        # --- 2. Zone de Transformation "Code to Doc" (Look Moderne) ---
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #f1f2f6;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(container)
        
        # Label de titre de la zone
        demo_title = QLabel("APERÇU DE LA TRANSFORMATION")
        demo_title.setStyleSheet("""
            font-weight: bold; 
            color: #2f3542;          
            font-size: 10px; 
            letter-spacing: 1px;      
            border: none;
            padding-bottom: 5px;
        """)
        container_layout.addWidget(demo_title)

        example_layout = QHBoxLayout()
        example_layout.setSpacing(0)

        # Éditeur de gauche (Dark Mode / Source)
        self.pseudo = QTextEdit()
        self.pseudo.setPlainText("# Intro\ntitle: 'Agro-Model'\nversion: '1.0'\nauthor: 'CIM-PIM'")
        self.pseudo.setReadOnly(True)
        self.pseudo.setMinimumHeight(140)
        self.pseudo.setStyleSheet("""
            QTextEdit {
                background-color: #2d3436;
                color: #fab1a0;
                font-family: 'Consolas', monospace;
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
                padding: 12px;
                border: 1px solid #333333;
            }
        """)

        # Flèche de liaison
        arrow_container = QWidget()
        arrow_container.setStyleSheet("background-color: #f1f2f6; border: none;")
        arrow_layout = QVBoxLayout(arrow_container)
        arrow = QLabel("→")
        arrow.setStyleSheet("font-size: 28px; color: #74b9ff; font-weight: bold; border: none;")
        arrow_layout.addWidget(arrow, 0, Qt.AlignCenter)

        # Éditeur de droite (Light Mode / Résultat)
        self.result = QTextEdit()
        self.result.setPlainText("# Documentation\n\n**Projet :** Agro-Model\n**Version :** 1.0\n**Equipe :** CIM-PIM")
        self.result.setReadOnly(True)
        self.result.setMinimumHeight(140)
        self.result.setStyleSheet("""
            QTextEdit {
                background-color: #636e72;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                padding: 12px;
                border: 1px solid #E0E0E0;
                border-left: none;              /* Fusionne avec le bloc de gauche */
            }
        """)

        example_layout.addWidget(self.pseudo, 2)
        example_layout.addWidget(arrow_container, 1)
        example_layout.addWidget(self.result, 2)
        
        container_layout.addLayout(example_layout)
        layout.addWidget(container)

        # --- 3. Badge d'Information ---
        self.footer_info = QLabel("✨ Support natif : Markdown, PDF, DOCX et HTML.")
        self.footer_info.setStyleSheet("""
            color: #57606f;          
            font-size: 11px; 
            font-weight: 600;         
            background-color: #e1e4e8; 
            padding: 5px 12px;
            border-radius: 15px;      
        """)
        layout.addWidget(self.footer_info)

        layout.addStretch()
        self.setLayout(layout)



class MetadataPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Identité du Document")
        self.setSubTitle("Définissez les propriétés officielles de votre documentation.")

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # --- 1. CORE INFO CARD (Two columns) ---
        core_card = QFrame()
        core_card.setStyleSheet("""
            QFrame { background-color: #f1f2f6; border: 1px solid #dcdde1; border-radius: 10px; padding: 10px; }
            QLabel { font-weight: bold; color: #34495e; border: none; }
            QLineEdit, QComboBox { background: white; border: 1px solid #ccc; border-radius: 4px; padding: 5px; }
        """)
        core_layout = QGridLayout(core_card)
        core_layout.setSpacing(10)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Nom du projet ou modèle...")
        
        #self.version_edit = QLineEdit("1.0.0")
        #self.version_edit.setFixedWidth(80)

        self.subtitle_edit = QLineEdit()
        self.subtitle_edit.setPlaceholderText("Complément d'information...")

        # Layout organization
        core_layout.addWidget(QLabel("Titre principal * :"), 0, 0)
        core_layout.addWidget(self.title_edit, 0, 1, 1, 3) # Spans 3 columns
        
        core_layout.addWidget(QLabel("Sous-titre :"), 1, 0)
        core_layout.addWidget(self.subtitle_edit, 1, 1, 1, 3)

        version_layout = QHBoxLayout()
        self.version_edit = QLineEdit("1.0.0")
        self.version_edit.setFixedWidth(70) # Fixed width prevents stretching
        version_layout.addWidget(QLabel("Version * :"))
        version_layout.addWidget(self.version_edit)
        version_layout.addStretch()
        
        status_layout = QHBoxLayout()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Brouillon", "Revue", "Final"])
        self.status_combo.setFixedWidth(100) # Fixed width for consistency
        status_layout.addWidget(QLabel("Statut :"))
        status_layout.addWidget(self.status_combo)
        status_layout.addStretch() 

        core_layout.addLayout(version_layout, 2, 0, 1, 2) 
        core_layout.addLayout(status_layout, 2, 2, 1, 2)

        main_layout.addWidget(core_card)

        # --- 2. TAGS & LANGUAGE (Horizontal) ---
        tags_layout = QHBoxLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["fr", "en"])
        self.language_combo.setFixedWidth(60)
        
        self.keywords_edit = QLineEdit()
        self.keywords_edit.setPlaceholderText("Mots-clés (séparés par des virgules)...")
        
        tags_layout.addWidget(QLabel("Langue :"))
        tags_layout.addWidget(self.language_combo)
        tags_layout.addSpacing(20)
        tags_layout.addWidget(QLabel("Mots clés :"))
        tags_layout.addWidget(self.keywords_edit, 1)
        
        main_layout.addLayout(tags_layout)

        # --- 3. AUTHORS MANAGEMENT ---
        authors_group = QGroupBox("👥 Liste des Contributeurs")
        authors_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2980b9; margin-top: 10px; }")
        authors_layout = QVBoxLayout()
        
        self.authors_list = QListWidget()
        self.authors_list.setMaximumHeight(100) # Prevents taking too much space
        self.authors_list.setStyleSheet("""
            QListWidget { border: 1px solid #eee; border-radius: 5px; background: #fafafa; }
            QListWidget::item { padding: 5px; border-bottom: 1px solid #f1f1f1; }
        """)

        btn_layout = QHBoxLayout()
        add_author_btn = QPushButton("+ Ajouter un auteur")
        add_author_btn.setMinimumWidth(150)
        # Apply our "Action Blue" hover style
        self.apply_button_style(add_author_btn, "#27ae60") # Green for "Add"
        
        remove_author_btn = QPushButton("- Supprimer sélection")
        self.apply_button_style(remove_author_btn, "#e74c3c") # Red for "Delete"

        btn_layout.addWidget(add_author_btn)
        btn_layout.addWidget(remove_author_btn)
        btn_layout.addStretch()

        authors_layout.addWidget(self.authors_list)
        authors_layout.addLayout(btn_layout)
        authors_group.setLayout(authors_layout)

        main_layout.addWidget(authors_group)
        main_layout.addStretch()
        self.setLayout(main_layout)

        # Fields & Connections
        self.registerField("doc_title*", self.title_edit)
        self.registerField("doc_version", self.version_edit)
        add_author_btn.clicked.connect(self.add_author_dialog)
        remove_author_btn.clicked.connect(self.remove_author)

    def apply_button_style(self, btn, hover_color):
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: #f1f2f6; border: 1px solid #dcdde1; border-radius: 4px; padding: 4px; }}
            QPushButton:hover {{ background-color: {hover_color}; color: white; }}
        """)

    def remove_author(self):
        """Standard UX: always allow users to fix a list entry"""
        for item in self.authors_list.selectedItems():
            self.authors_list.takeItem(self.authors_list.row(item))

    def add_author_dialog(self):
        """Dialogue simple pour ajouter un auteur"""
        d = QDialog(self)
        d.setWindowTitle("Ajouter un auteur")

        layout = QFormLayout()

        name_edit = QLineEdit()
        affiliation_edit = QLineEdit()
        role_edit = QLineEdit("Auteur principal")
        email_edit = QLineEdit()

        layout.addRow("Nom complet *:", name_edit)
        layout.addRow("Affiliation :", affiliation_edit)
        layout.addRow("Rôle :", role_edit)
        layout.addRow("Email :", email_edit)

        btn_box = QHBoxLayout()
        ok_btn = QPushButton("Ajouter")
        cancel_btn = QPushButton("Annuler")

        def add():
            name = name_edit.text().strip()
            if name:
                item_text = f"{name} — {affiliation_edit.text().strip() or '—'} — {role_edit.text().strip()} — {email_edit.text().strip() or '—'}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, {
                    "name": name,
                    "affiliation": affiliation_edit.text().strip(),
                    "role": role_edit.text().strip(),
                    "email": email_edit.text().strip()
                })
                self.authors_list.addItem(item)
            d.accept()  # ferme le dialog proprement

        ok_btn.clicked.connect(add)
        cancel_btn.clicked.connect(d.reject)  # ferme le bon dialog

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)
        layout.addRow(btn_box)

        d.setLayout(layout)
        d.exec()


class SectionsConfigPage(QWizardPage):
    # Dans SectionsConfigPage.__init__
    def __init__(self):
        super().__init__()
        self.setTitle("Configuration des Sections")
        self.setSubTitle("Définissez les sources de données pour chaque chapitre.")

        # 1. On utilise un ScrollArea pour le responsive
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame) # Plus moderne sans bordure double
        
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setSpacing(15) # Espace entre les blocs
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.section_widgets = {}

        sections = [
            ("Introduction", ["YAML", "JSON"]),
            ("Modele_Conceptuel", ["XMI"]),
            ("Initialisation", ["YAML", "JSON", "Multi-CSV"]),
            ("Indicateurs", ["YAML", "CSV", "JSON"]),
            ("Mode_Emploi", ["YAML", "JSON"])
        ]

        HELP_TIPS = {
            "Introduction": "Décrivez les objectifs et le contexte de votre projet. Prend en charge la mise en forme de texte enrichi.",
            "Modele_Conceptuel": "Le noyau architectural. Fournissez un fichier XMI exporté de votre DSL Socio-Ecosystem.",
            "Initialisation": "Données de configuration ou variables globales. Pour Multi-CSV, sélectionnez le dossier ROOT contenant les fichiers.",
            "Indicateurs": "Les métriques quantitatives. Assurez-vous que votre fichier CSV utilise le séparateur interne correct (|) pour les variables imbriquées.",
            "Mode_Emploi": "Guide utilisateur ou manuel technique. Généralement une description générale pour les utilisateurs finaux.",
            "formats": {
                "YAML": "Idéal pour les configurations lisibles par l'humain.",
                "JSON": "Format standard pour l'échange de données structurées.",
                "CSV": "Données tabulaires. Rapide et facile à modifier dans Excel.",
                "XMI": "Format d'échange basé sur XML pour les modèles.",
                "Multi-CSV": "Mode spécial: analyse un répertoire entier à la recherche de fichiers CSV associés. "
            }
        }

        for sec_name, formats in sections:
            # Utilisation d'un widget conteneur stylisé plutôt qu'un GroupBox lourd
            section_card = QFrame()
            section_card.setObjectName("SectionCard")
            section_card.setStyleSheet("""
                #SectionCard {
                    background-color: transparent; 
                    border: 1px solid #dcdde1; 
                    border-radius: 10px;
                    padding: 5px;
                }
            """)
            
            card_layout = QVBoxLayout(section_card)
            
            # --- Entête de la section (Titre + Format) ---
            header_layout = QHBoxLayout()
            title_label = QLabel(sec_name.replace("_", " "))
            title_label.setStyleSheet("font-weight: bold; color: #3498db; font-size: 13px;")
            title_label.setToolTip(HELP_TIPS.get(sec_name, ""))
            title_label.setCursor(Qt.WhatsThisCursor)
            
            format_combo = QComboBox()
            format_combo.addItems(formats)
            format_combo.setFixedWidth(120) # Compact
            format_combo.setToolTip(HELP_TIPS['formats'].get(format_combo.currentText(), ""))

            # We update the tooltip whenever the user changes the format
            def update_combo_tip(text, cb=format_combo):
                cb.setToolTip(HELP_TIPS['formats'].get(text, "Format pris en charge pour cette section."))
            
            format_combo.currentTextChanged.connect(update_combo_tip)
                    
            header_layout.addWidget(title_label)
            header_layout.addStretch()
            header_layout.addWidget(QLabel("Format:"))
            header_layout.addWidget(format_combo)
            
            # --- Ligne Chemin (Input + Status + Browse) ---
            path_layout = QHBoxLayout()

            path_edit = QLineEdit()
            path_edit.setPlaceholderText("Chemin du fichier...")
            path_edit.setToolTip(f"Chemin du fichier pour {sec_name.replace('_', ' ')}")
            path_edit.setMinimumHeight(35)
            
            status_icon = QLabel("⚪")
            status_icon.setFixedWidth(30)
            status_icon.setAlignment(Qt.AlignCenter)
            status_icon.setToolTip("Vérification de l'accessibilité des fichiers...")
            
            browse_btn = QPushButton("Parcourir...") # Bouton minimaliste
            browse_btn.setMinimumWidth(100) 
            browse_btn.setToolTip(f"Selectionner le repertoire pour {sec_name.replace('_', ' ')}")
            
            path_layout.addWidget(path_edit, 1)
            path_layout.addWidget(status_icon)
            path_layout.addWidget(browse_btn)

            # --- Ligne Optionnelle (Séparateur) ---
            # On la crée de manière très compacte
            sep_container = QWidget()
            sep_layout = QHBoxLayout(sep_container)
            sep_layout.setContentsMargins(35, 0, 0, 5) 

            sep_edit = QLineEdit(",")
            sep_edit.setFixedWidth(30)
            sep_edit.setAlignment(Qt.AlignCenter)

            sep_layout.addStretch()
            sep_layout.addWidget(QLabel("Séparateur CSV:"))
            sep_layout.addWidget(sep_edit)
            sep_container.setVisible(False)

            # Logique de visibilité
            format_combo.currentTextChanged.connect(
                lambda t, c=sep_container: c.setVisible(t in ["CSV", "Multi-CSV"])
            )
            
            card_layout.addLayout(header_layout)
            card_layout.addLayout(path_layout)
            card_layout.addWidget(sep_container)
                       

            def make_browse(key, edit, combo, sep_widget):
                def browse():
                    # 1. Définition des filtres selon la section
                    if key == "Modele_Conceptuel":
                        file, _ = QFileDialog.getOpenFileName(
                            self, f"Sélectionner le {key}", "", "Fichiers XMI (*.xmi)"
                        )
                    elif key == "Initialisation":
                        # Création d'une boîte de dialogue pour demander le type de source
                        msg_box = QMessageBox(self)
                        msg_box.setWindowTitle("Type d'Initialisation")
                        msg_box.setText("Comment souhaitez-vous charger les données d'initialisation ?")
                        
                        # Ajout des boutons personnalisés
                        btn_folder = msg_box.addButton("Dossier (CSV)", QMessageBox.ActionRole)
                        btn_file = msg_box.addButton("Fichier unique (YAML/JSON)", QMessageBox.ActionRole)
                        msg_box.addButton("Annuler", QMessageBox.RejectRole)
                        
                        msg_box.exec_()
                        
                        if msg_box.clickedButton() == btn_folder:
                            # Option Dossier
                            file = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier contenant les CSV")
                        elif msg_box.clickedButton() == btn_file:
                            # Option Fichier classique
                            file, _ = QFileDialog.getOpenFileName(
                                self, "Sélectionner le fichier d'initialisation", "", 
                                "Fichiers supportés (*.yml *.json);;YAML (*.yml);;JSON (*.json)"
                            )
                        else:
                            return  # L'utilisateur a annulé
                    elif key == "Indicateurs":
                        file, _ = QFileDialog.getOpenFileName(
                            self, f"Sélectionner le fichier de données pour {key}", "", "Tous supportés (*.csv *.yml *.json);;Fichiers YAML (*.yml);;Fichiers JSON (*.json);;Fichiers CSV (*.csv)"
                        )
                    elif key in ["Introduction", "Mode_Emploi"]:
                        file, _ = QFileDialog.getOpenFileName(
                            self, f"Sélectionner le fichier de données pour {key}", "", "Tous supportés (*.yml *.json);;Fichiers YAML (*.yml);;Fichiers JSON (*.json)"
                        )
                    
                    if file:
                        # 2. Mise à jour du champ de texte
                        edit.setText(file)

                        # 3. Auto-sélection du format dans le combo
                        if os.path.isdir(file):
                            # On cherche "Multi-CSV" ou "CSV" selon votre nomenclature
                            index_csv = combo.findText("Multi-CSV")
                            if index_csv < 0:  # Repli si Multi-CSV n'existe pas
                                index_csv = combo.findText("CSV")
                            
                            if index_csv >= 0:
                                combo.setCurrentIndex(index_csv)
                        else:
                            # Extraction et normalisation de l'extension
                            ext = file.split('.')[-1].lower()
                            
                            # Mapping : Extension fichier -> Texte exact dans le QComboBox
                            extension_map = {
                                'yml': 'YAML',
                                'yaml': 'YAML',
                                'json': 'JSON',
                                'csv': 'CSV',
                                'xmi': 'XMI'
                            }
                            
                            target_text = extension_map.get(ext)
                            
                            if target_text:
                                index = combo.findText(target_text)
                                if index >= 0:
                                    combo.setCurrentIndex(index)

                        self.update_separator_visibility(key, combo, sep_widget)  # Mise à jour de l'UI
                return browse
        
            # Connexions
            path_edit.textChanged.connect(lambda text, lbl=status_icon: self.validate_path(text, lbl))
            browse_btn.clicked.connect(make_browse(sec_name, path_edit, format_combo, sep_edit))
            
            self.main_layout.addWidget(section_card)
            self.section_widgets[sec_name] = (format_combo, path_edit, sep_edit)
            
        self.main_layout.addStretch()
        
        # Finalisation du scroll
        scroll.setWidget(container)
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll)


    def update_separator_visibility(self, key, combo, sep_widget):
        # On affiche le champ séparateur uniquement si CSV est sélectionné
        is_csv = (combo.currentText() in ["CSV", "Multi-CSV"])
        sep_widget.setVisible(is_csv) 
                    
        # Optionnel : Mettre ';' par défaut si c'est un dossier (standard Excel FR)
        if is_csv and os.path.isdir(Path(key)):
            sep_widget.setText(";") 
        else:
            sep_widget.setText(",")

    def validate_path(self, path, label):
        if not path:
            label.setText("⚪")
            label.setToolTip("Aucun fichier sélectionné")
        elif os.path.exists(path):
            label.setText("✅")
            size = os.path.getsize(path) / 1024
            label.setToolTip("Fichier/Dossier trouvé : {size:.1f} KB\nChemin: {path}")
        else:
            label.setText("❌")
            label.setToolTip("Erreur: Fichier introuvable. Veuillez vérifier le chemin d'accès ou les autorisations.")


class ExportPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Configuration des Sorties")
        self.setSubTitle("Définissez les formats de fichiers et les styles visuels.")

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # ====================== 1. FORMATS D'EXPORT (GRID) ======================
        format_group = QGroupBox("Formats de documents")
        format_group.setStyleSheet("QGroupBox { font-weight: bold; color: #34495e; }")
        
        # We use a Grid for a cleaner "Control Panel" look
        grid = QGridLayout()
        grid.setContentsMargins(15, 15, 15, 15)
        grid.setSpacing(20)

        # Style for the "Yes/No" combos to make them look like toggles
        combo_style = "QComboBox { padding: 4px; min-width: 60px; }"

        self.html_cb = QComboBox(); self.html_cb.addItems(["Non", "Oui"]); self.html_cb.setCurrentText("Oui")
        self.pdf_cb  = QComboBox(); self.pdf_cb.addItems(["Non", "Oui"]);  self.pdf_cb.setCurrentText("Oui")
        self.docx_cb = QComboBox(); self.docx_cb.addItems(["Non", "Oui"]); self.docx_cb.setCurrentText("Oui")
        
        for cb in [self.html_cb, self.pdf_cb, self.docx_cb]:
            cb.setStyleSheet(combo_style)

        # Labels with Icons (Emojis work great for modern UI)
        grid.addWidget(QLabel("🌐 HTML Interactif :"), 0, 0)
        grid.addWidget(self.html_cb, 0, 1)
        grid.addWidget(QLabel("📕 Format PDF :"), 0, 2)
        grid.addWidget(self.pdf_cb, 0, 3)
        grid.addWidget(QLabel("📘 Microsoft Word :"), 1, 0)
        grid.addWidget(self.docx_cb, 1, 1)
        
        format_group.setLayout(grid)
        layout.addWidget(format_group)

        # ====================== 2. DESTINATION & STYLE (CARDS) ======================
        # Combined container for Path and CSS
        settings_card = QFrame()
        settings_card.setStyleSheet("""
            QFrame { 
                background-color: #f1f2f6; 
                border: 1px solid #dcdde1; 
                border-radius: 10px; 
            }
            QLabel { border: none; font-weight: 500; }
        """)
        card_layout = QVBoxLayout(settings_card)
        card_layout.setSpacing(15)

        # --- Output Directory Row ---
        output_row = QVBoxLayout()
        output_label_layout = QHBoxLayout()
        output_label_layout.addWidget(QLabel("📂 Dossier de destination :"))
        output_label_layout.addStretch()
        
        path_input_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(str(Path("exports").resolve()))
        self.output_dir_edit.setPlaceholderText("Sélectionnez un dossier...")
        
        browse_out_btn = QPushButton("Parcourir...")
        browse_out_btn.setMinimumWidth(100)
        browse_out_btn.clicked.connect(self.browse_output_directory)

        path_input_layout.addWidget(self.output_dir_edit, 1)
        path_input_layout.addWidget(browse_out_btn)
        
        output_row.addLayout(output_label_layout)
        output_row.addLayout(path_input_layout)
        card_layout.addLayout(output_row)

        # --- CSS Style Row ---
        css_row = QVBoxLayout()
        css_label_layout = QHBoxLayout()
        css_label_layout.addWidget(QLabel("🎨 Style personnalisé (CSS) :"))
        css_label_layout.addStretch()

        css_input_layout = QHBoxLayout()
        self.css_edit = QLineEdit()
        self.css_edit.setPlaceholderText("Laissez vide pour le style par défaut...")
        
        browse_css_btn = QPushButton("Parcourir...")
        browse_css_btn.setMinimumWidth(100)
        browse_css_btn.clicked.connect(self.browse_css)

        css_input_layout.addWidget(self.css_edit, 1)
        css_input_layout.addWidget(browse_css_btn)

        css_row.addLayout(css_label_layout)
        css_row.addLayout(css_input_layout)
        card_layout.addLayout(css_row)

        layout.addWidget(settings_card)
        layout.addStretch()
        self.setLayout(layout)

    def browse_output_directory(self):
        """Sélection du dossier de sortie"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier de sortie",
            self.output_dir_edit.text() or str(Path.home()),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder:
            self.output_dir_edit.setText(folder)

    def browse_css(self):
        file, _ = QFileDialog.getOpenFileName(None, "Choisir un fichier CSS", "", "CSS Files (*.css)")
        if file:
            self.css_edit.setText(file)

    def get_output_dir(self) -> str:
        """Retourne le dossier de sortie choisi par l'utilisateur"""
        return self.output_dir_edit.text().strip()

    def get_export_formats(self) -> list:
        """Retourne la liste des formats sélectionnés"""
        formats = []
        if self.html_cb.currentText() == "Oui":
            formats.append("html")
        if self.pdf_cb.currentText() == "Oui":
            formats.append("pdf")
        if self.docx_cb.currentText() == "Oui":
            formats.append("docx")
        return formats

    def get_css_path(self) -> Optional[str]:
        """Retourne le chemin CSS ou None"""
        path = self.css_edit.text().strip()
        return path if path else None


class SummaryPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Confirmation du Plan de Génération")
        self.setSubTitle("Veuillez sur les détails de génération avant de lancer le moteur.")

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Widget de contenu avec un style "Dashboard"
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

        # Zone d'alerte dynamique (si fichiers manquants par exemple)
        self.warning_box = QLabel()
        self.warning_box.setWordWrap(True)
        self.warning_box.setVisible(False)
        self.warning_box.setStyleSheet("""
            background-color: #feeef1;
            color: #d63031;
            border: 1px solid #fab1a0;
            padding: 12px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12;
        """)

        # Petit bandeau d'avertissement final
        self.info_box = QLabel("💡 Astuce : Vérifiez que les fichiers sources ne sont pas ouverts dans une autre application.")
        self.info_box.setWordWrap(True)
        self.info_box.setStyleSheet("""
            background-color: #e1e4e8;
            color: #57606f;
            font-style: italic;
            font-size: 12px;
            padding: 5px 12px;
            border: 1px solid #fab1a0;
            border-radius: 6px;
        """)

        layout.addWidget(self.content_area)
        layout.addWidget(self.warning_box)
        layout.addWidget(self.info_box)

        layout.addStretch()
        self.setLayout(layout)

    def initializePage(self):
        """
        Cette méthode est appelée par le Wizard à CHAQUE FOIS 
        que l'utilisateur arrive sur cette page.
        """
        wizard = self.wizard()
        
        # 1. Infos de base
        title = self.field('doc_title')
        version = self.field('doc_version')
        output = wizard.export_page.get_output_dir()

        export_formats = wizard.export_page.get_export_formats()

        # On crée une liste d'affichage qui contient TOUJOURS Markdown
        display_formats = ["MARKDOWN"] 

        # Transformation en texte lisible (ex: PDF, DOCX)
        if export_formats:
            for f in export_formats:
               if f.upper() != "MARKDOWN": 
                   display_formats.append(f.upper())
        format_text = " ".join(display_formats)

        
        # 2. Analyse des sections
        active_sections = []
        for name, widgets in wizard.sections_page.section_widgets.items():
            # On récupère le QLineEdit qui est en deuxième position (index 1)
            path_edit = widgets[1] 
            path = path_edit.text().strip()
            if path:
                active_sections.append((name, os.path.basename(path)))

        # --- CONSTRUCTION DU HTML ---
        html = f"""
        <table width='100%' cellpadding='8'>
            <tr>
                <td colspan='2' style='font-size: 14px; font-weight: bold; color: #3498db; text-transform: uppercase; letter-spacing: 1px;'>
                    🎯 Plan de Génération
                </td>
            </tr>
            <tr>
                <td width='40%' style='color: #57606f; font-weight: bold; white-space: nowrap;'>Nom du Projet :</td>
                <td style='color: #2f3542; font-weight: bold;'>{title} <span style='color: #74b9ff;'>v{version}</span></td>
            </tr>
            <tr>
                <td width='40%' style='color: #57606f; font-weight: bold; white-space: nowrap;'>Formats d'export :</td>
                <td style='color: #e67e22; font-weight: bold;'>{format_text}</td>
            </tr>
            <tr>
                <td width='40%' style='color: #57606f; font-weight: bold; white-space: nowrap;'>Dossier de sortie :</td>
                <td style='font-family: Consolas, monospace; font-size: 11px; color: #218c74;'>{output}</td>
            </tr>
            <tr><td colspan='2'><hr style='border: 0; border-top: 1px solid #dcdde1; margin: 10px 0;'></td></tr>
            <tr>
                <td colspan='2' style='font-size: 14px; font-weight: bold; color: #3498db; text-transform: uppercase; letter-spacing: 1px; padding-top: 10px;'>
                    📦 Structure du Document ({len(active_sections)} sections)
                </td>
            </tr>
        """

        for name, filename in active_sections:
            html += f"""
            <tr>
                <td width='40%' style='color: #57606f; white-space: nowrap;'>{name}</td>
                <td style='font-family: Consolas, monospace; font-size: 12px; color: #2d3436;'>{filename}</td>
            </tr>
            """

        html += "</table>"
        self.content_area.setText(html)

        # 3. Gestion des alertes UX
        if not active_sections:
            # CAS 1 : Erreur (Aucune section)
            self.warning_box.setText("⚠️ ATTENTION : Aucune section configurée. Le document sera vide.")
            self.warning_box.setVisible(True)
            self.info_box.setVisible(False)  # On cache l'astuce car il y a une erreur
        else:
            # CAS 2 : Tout est OK
            self.warning_box.setVisible(False)
            self.info_box.setVisible(True)   # On affiche l'astuce préventive


class LogPage(QWizardPage):
    def __init__(self, log_widget, parent=None):
        super().__init__(parent)
        self.setTitle("Console d'Exécution")
        self.setSubTitle("Processus de compilation et génération des livrables.")
        
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Conteneur pour la console avec un effet de bordure
        self.console_frame = QGroupBox("Terminal de sortie")
        self.console_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                text-transform: uppercase;
                color: #5dade2;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }
        """)
        
        frame_layout = QVBoxLayout()
        # Personnalisation du log_widget (le QTextEdit)
        log_widget.setStyleSheet("""
            QTextEdit {
                background-color: #0f1419; /* Bleu/Noir très profond */
                color: #abb2bf;           /* Gris clair syntaxe */
                font-family: 'Consolas', 'Monaco', 'Courier New';
                font-size: 10pt;
                border: none;
                padding: 10px;
            }
        """)
        frame_layout.addWidget(log_widget)
        self.console_frame.setLayout(frame_layout)
        
        # Pied de page avec barre de statut stylisée
        status_layout = QHBoxLayout()
        self.status_label = QLabel("INITIALISATION DU MOTEUR...")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                color: #2ecc71;
                font-family: 'Segoe UI', sans-serif;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
                border-left: 4px solid #2ecc71;
            }
        """)
        
        # Ajout d'un petit indicateur de "pulse" ou version texte
        self.version_label = QLabel("SYSTEM v1.0")
        self.version_label.setStyleSheet("color: #555; font-size: 9px;")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.version_label)

        layout.addWidget(self.console_frame)
        layout.addLayout(status_layout)
        self.setLayout(layout)

    def set_status(self, text, color="#2ecc71"):
        """Met à jour le texte et la couleur de la barre de statut"""
        self.status_label.setText(text.upper())
        self.status_label.setStyleSheet(f"""
            background-color: #1a1a1a;
            color: {color};
            font-weight: bold;
            padding: 8px 15px;
            border-radius: 4px;
            border-left: 4px solid {color};
        """)


    def set_status(self, text):
        self.status_label.setText(text)

    def isComplete(self):
        # Le bouton "Terminer" ne s'active que si le processus est fini
        return getattr(self.wizard(), 'generation_finished', False)

    def validatePage(self):
        # Empêche le retour en arrière si la génération est en cours
        return getattr(self.wizard(), 'generation_finished', False)

# ========================== Classe principale ==========================

class SetupWizardDoc(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Générateur de Documentation")
        self.setWizardStyle(QWizard.ModernStyle)

        # Ajout de l'icône d'application
        self.setWindowIcon(self.load_app_icon())

        # Options du wizard
        self.setOption(QWizard.NoBackButtonOnStartPage, True)      # Back cliquable dès la première page
        self.setOption(QWizard.DisabledBackButtonOnLastPage, False) # Back cliquable sur la dernière page
        self.setOption(QWizard.IndependentPages, True)              # Navigation totalement libre (Back/Next toujours actifs)
        self.setOption(QWizard.HaveHelpButton, False)          # Pas de bouton d'aide (on peut le réactiver si besoin)
        
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
        self.resize(850, 720)  # Taille initiale plus grande pour éviter les problèmes d'affichage sur certains écrans
        self.setMinimumSize(800, 680)  # Taille minimale pour éviter les problèmes d'affichage
        self.center_on_screen()

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
        self.intro_page = IntroDocPage()
        self.metadata_page = MetadataPage()
        self.sections_page = SectionsConfigPage()
        self.export_page = ExportPage()
        self.summary_page = SummaryPage() 
        self.log_page = LogPage(self.log_console) 

        # 3. Ajouter les pages au Wizard
        self.addPage(self.intro_page)
        self.addPage(self.metadata_page)
        self.addPage(self.sections_page)
        self.addPage(self.export_page)
        self.addPage(self.summary_page)
        self.addPage(self.log_page)

        # Traduction des boutons en français
        self.setButtonText(QWizard.BackButton, "Précédent")
        self.setButtonText(QWizard.NextButton, "Suivant")
        self.setButtonText(QWizard.CommitButton, "Suivant")
        self.setButtonText(QWizard.FinishButton, "Terminer")
        self.setButtonText(QWizard.CancelButton, "Annuler")

        # Connexion pour changer dynamiquement le texte du bouton Suivant
        self.currentIdChanged.connect(self._handle_ui_updates)
        self.button(QWizard.NextButton).clicked.connect(self._on_next_clicked)

    def _on_next_clicked(self):
        """Gère l'action du bouton Suivant de manière déterministe"""
        # Dans votre ordre : 0:Intro, 1:Metadata, 2:Sections, 3:Export, 4:Summary 5:Log
        btn_text = self.button(QWizard.NextButton).text()
        
        if self.currentId() == 5 and "Lancer" in btn_text:
            # On ne laisse pas le wizard avancer tout seul
            # On lance notre logique personnalisée
            self.start_generation() 
        else:
            pass


    def _handle_ui_updates(self, current_id):
        """Met à jour uniquement l'aspect visuel des boutons"""
        # ID 4 = SummaryPage | ID 5 = LogPage
        
        # 1. Gestion du texte du bouton principal
        if current_id == 4:
            # On force la page de résumé à se rafraîchir
            self.summary_page.initializePage()
            self.setButtonText(QWizard.NextButton, "Lancer la génération")
        elif current_id == 5:
            # Sur la dernière page, le NextButton devient FinishButton
            self.setButtonText(QWizard.FinishButton, "Terminer")
        else:
            self.setButtonText(QWizard.NextButton, "Suivant")

        # 2. Gestion de la navigation (Précédent / Annuler)
        back_btn = self.button(QWizard.BackButton)
        cancel_btn = self.button(QWizard.CancelButton)
        
        if current_id == 5: # Page de Logs
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
        """Sauvegarde la configuration au format exact de ton exemple"""

        metadata_page = self.page(1)  # MetadataPage

        # Métadonnées
        keywords_text = metadata_page.keywords_edit.text().strip()
        keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]

        # Auteurs
        authors = []
        for i in range(metadata_page.authors_list.count()):
            item = metadata_page.authors_list.item(i)
            data = item.data(Qt.UserRole)
            if data:
                authors.append(data)

        config = {
            "metadata": {
                "title": metadata_page.title_edit.text().strip() or "Modèle sans titre",
                "subtitle": metadata_page.subtitle_edit.text().strip(),
                "version": metadata_page.version_edit.text().strip() or "1.0.0",
                "date_creation": datetime.now().strftime("%Y-%m-%d"),
                "date_version": datetime.now().strftime("%Y-%m-%d"),
                "status": metadata_page.status_combo.currentText(),
                "classification": "Interne",
                "language": metadata_page.language_combo.currentText(),
                "keywords": keywords
            },
            "authors": authors,
            "project": {},
            "documentation": {},
            "technical": {},
            "paths": {},
            "assets": {},
            "schemas": {},
            "export": {
                "formats": [],
                "css_path": None,
                "output_dir": "exports"
            }
        }

        # === Sections ===
        sections_page = self.page(2)  # SectionsConfigPage
        for sec_key, widgets in sections_page.section_widgets.items():
            # Si vous avez 3 widgets, l'unpackaging ressemble à ça :
            fmt_combo, path_edit, sep_edit = widgets 
            
            input_path = path_edit.text().strip()
            if not input_path:
                continue

            current_format = fmt_combo.currentText()
            
            section_data = {
                "input_path": input_path,
                "format": current_format.lower(),
                "ignored": False
            }

            # --- SAUVEGARDE DU DÉLIMITEUR ---
            if current_format in ["CSV", "Multi-CSV"]:
                # On récupère le texte, si c'est vide on met une virgule par défaut
                delim = sep_edit.text() if sep_edit.text() else ","
                section_data["delimitor"] = delim
                

            config["paths"][sec_key] = section_data

        # === Export + Dossier de sortie ===
        export_page = self.page(3)  # ExportPage

        config["export"]["formats"] = export_page.get_export_formats()
        config["export"]["css_path"] = export_page.get_css_path()
        
        # Utilisation du dossier choisi par l'utilisateur
        output_dir = export_page.get_output_dir()

        if output_dir:
            config["export"]["output_dir"] = output_dir

        # Mise à jour du output_path principal avec le dossier choisi
        if output_dir:
            config["paths"]["output_path"] = str(Path(output_dir) / 
                f"documentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")

        # Sauvegarde
        try:
            #self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open("config_documentation.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            #QMessageBox.information(self, "Configuration", "config_documentation.json sauvegardé avec succès !")
            #print(f"✅ config_documentation.json sauvegardé ({len(config['paths'])} sections)")
            return True
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de sauvegarder config_documentation.json :\n{str(e)}")
            return False


    def start_generation(self):
        """Lance la génération et bascule sur la page de logs"""
        # 1. Sauvegarde
        if not self.save_config():
            return
        
        # 2. Préparation de l'état
        self.generation_finished = False
        self.log_console.clear()
        self.log_console.append("<b>[SYSTEM]</b> Initialisation du moteur de génération...")

        # 3. Transition UI
        # On passe à la page suivante (LogPage) AVANT de lancer le processus
        self.next() 
        
        # On change le texte du bouton : il devient "Terminer"
        self.setButtonText(QWizard.FinishButton, "Terminer")
        # On le désactive le temps de la génération pour respecter l'UX
        self.button(QWizard.FinishButton).setEnabled(False)
        # On désactive aussi le bouton retour pour éviter de casser le process
        self.button(QWizard.BackButton).setEnabled(False)

        # 4. Lancement du processus
        try:
            project_root = Path(__file__).resolve().parent.parent

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
            self.process.setArguments(["main_doc.py"])

            # Connexions
            self.process.readyReadStandardOutput.connect(self.read_stdout)
            self.process.readyReadStandardError.connect(self.read_stderr)
            self.process.finished.connect(self.on_generation_finished)

            self.process.start()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lancer la génération :\n{str(e)}")

    def read_stdout(self):
        raw = self.process.readAllStandardOutput()
        try:
            output = bytes(raw).decode("utf-8", errors="replace").strip()
        except:
            output = bytes(raw).decode("latin-1", errors="replace").strip()
            
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
            error = bytes(raw).decode("utf-8", errors="replace").strip()
        except:
            error = bytes(raw).decode("latin-1", errors="replace").strip()
            
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
        """Appelée quand le script main_doc.py s'arrête"""
        self.generation_finished = True

        # On ferme la petite barre de progression flottante
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        # Mise à jour du statut sur la LogPage
        if exit_code == 0:
            self.log_page.set_status("Génération terminée !")
            self.log_console.append("<br><span style='color: #2ecc71;'><b>[SUCCESS]</b> Opération terminée avec succès.")
        else:
            self.log_page.set_status("Echec de la génération.")
            self.log_console.append("<br><span style='color: #e06c75;'><b>[ERROR]</b> Le processus s'est arrêté avec des erreurs.")

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
