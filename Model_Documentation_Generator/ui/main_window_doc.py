#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import subprocess
from pathlib import Path
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWizard, QStyleFactory
from PySide6.QtGui import QIcon, QPalette, QColor, QPixmap
from PySide6.QtCore import QSettings, Qt


# Configuration du chemin du projet
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
sys.path.insert(0, str(project_root))

# Import du wizard de documentation
from ui.setup_wizard_doc import SetupWizardDoc

# ====================== CONFIGURATION LOGGING ======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DocumentationGenerator")


# ====================== THÈMES (cohérents avec GAML) ======================
def apply_modern_light_theme(app):
    """Thème clair moderne"""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(250, 250, 250))
    palette.setColor(QPalette.WindowText, QColor(40, 40, 40))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(40, 40, 40))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor(40, 40, 40))
    app.setPalette(palette)

    app.setStyleSheet("""
        QWizard, QWizardPage {
            background-color: #fafafc;
            color: #2d2d37;
        }
        
        QLabel {
            font-size: 14px;
            color: #2d2d37;
            padding: 4px;
        }
        
        QLineEdit, QComboBox, QSpinBox {
            padding: 8px 10px;
            border: 1px solid #c0c4cc;
            border-radius: 6px;
            background-color: #ffffff;
            color: #2d2d37;
            selection-background-color: #4a8cff;
        }
        
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #4a8cff;
        }
        
        QPushButton {
            background-color: #f1f2f6;   
            color: #2f3542;              
            border: 1px solid #dcdde1;
            border-radius: 6px;
            padding: 5px 15px;
            font-weight: 500;
        }
        
        
        QPushButton:hover {
            background-color: #3498db;   
            color: #ffffff;              
            border-color: #2980b9;       
        }
        
        QPushButton:pressed {
            background-color: #2980b9;   
        }
        
        QPushButton:disabled {
            background-color: #c0c4cc;
            color: #88888f;
        }
        
        /* Cadres pour pseudo-code et GAML */
        QFrame[frameShape="StyledPanel"] {
            background-color: #ffffff;
            border: 1px solid #d0d4dc;
            border-radius: 8px;
        }
        
        /* Style spécifique pour le pseudo-code (fond sombre pour contraste) */
        QLabel[pseudo="true"] {
            background-color: #2d3748;
            color: #e2e8f0;
            padding: 12px;
            border-radius: 6px;
            font-family: 'Consolas', 'Courier New', monospace;
        }
        
        /* Style pour le code GAML (fond bleu très clair) */
        QLabel[gaml="true"] {
            background-color: #f0f7ff;
            color: #1e3a8a;
            padding: 12px;
            border-radius: 6px;
            font-family: 'Consolas', 'Courier New', monospace;
        }
        
        QProgressBar {
            border: 1px solid #c0c4cc;
            border-radius: 6px;
            background-color: #f4f4f8;
            text-align: center;
            height: 18px;
        }
        
        QProgressBar::chunk {
            background-color: #4a8cff;
            border-radius: 5px;
        }
        
        /* Titres des pages */
        QWizardPage QLabel {
            font-size: 12px;
            font-weight: bold;
            color: #1f2937;
        }
        QGroupBox {
            font-weight: bold;
            margin-top: 16px;
            border: 1px solid #bdc3c7;
            border-radius: 6px;
            padding: 12px;
        }
        QToolTip {
            border: 1px solid #3498db;
            padding: 5px;
            border-radius: 3px;
            font-family: 'Segoe UI';
        }
    """)



def apply_modern_dark_theme(app: QApplication):
    """Applique un thème dark moderne et cohérent pour toute l'application"""
    
    # 1. Palette principale (Dark)
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(40, 40, 45))          # Fond principal
    palette.setColor(QPalette.WindowText, QColor(240, 240, 245))   # Texte principal
    palette.setColor(QPalette.Base, QColor(28, 28, 33))            # Fond des champs (QLineEdit, etc.)
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 50))
    palette.setColor(QPalette.ToolTipBase, QColor(50, 50, 55))
    palette.setColor(QPalette.ToolTipText, QColor(240, 240, 245))
    palette.setColor(QPalette.Text, QColor(240, 240, 245))
    palette.setColor(QPalette.Button, QColor(60, 60, 70))          # Boutons
    palette.setColor(QPalette.ButtonText, QColor(240, 240, 245))
    palette.setColor(QPalette.Highlight, QColor(80, 140, 220))     # Sélection / focus
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.Link, QColor(100, 180, 255))

    app.setPalette(palette)

    # 2. StyleSheet moderne et détaillé (prioritaire sur la palette)
    app.setStyleSheet("""
        QWizard, QWizardPage {
            background-color: #28282d;
            color: #f0f0f5;
        }
        
        QLabel {
            font-size: 14px;
            color: #e0e0e8;
            padding: 4px;
        }
        
        QLineEdit, QComboBox, QSpinBox {
            padding: 8px 10px;
            border: 1px solid #55555f;
            border-radius: 6px;
            background-color: #32323a;
            color: #f0f0f5;
            selection-background-color: #5088dd;
        }
        
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #5088dd;
        }
        
        QPushButton {
            background-color: #f1f2f6;   
            color: #2f3542;              
            border: 1px solid #dcdde1;
            border-radius: 6px;
            padding: 5px 15px;
            font-weight: 500;
        }
        
        
        QPushButton:hover {
            background-color: #3498db;   
            color: #ffffff;              
            border-color: #2980b9;       
        }
        
        QPushButton:pressed {
            background-color: #2980b9;   
        }

        
        QPushButton:disabled {
            background-color: #44444f;
            color: #88888f;
        }
        
        QFrame[frameShape="StyledPanel"] {
            background-color: #32323a;
            border: 1px solid #55555f;
            border-radius: 8px;
        }
        
        QProgressBar {
            border: 1px solid #55555f;
            border-radius: 6px;
            background-color: #32323a;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #5088dd;
            border-radius: 5px;
        }
        
        /* Style pour les titres de pages */
        QWizardPage[title] QLabel {
            font-size: 12px;
            font-weight: bold;
            color: #ffffff;
        }
        QGroupBox {
            font-weight: bold;
            margin-top: 16px;
            border: 1px solid #55555f;
            border-radius: 6px;
            padding: 12px;
        }
        QToolTip {
            border: 1px solid #3498db;
            padding: 5px;
            border-radius: 3px;
            font-family: 'Segoe UI';
        }
    """)


def is_dark_mode_system() -> bool:
    """Détecte si le système est en mode sombre"""
    try:
        palette = QApplication.palette()
        return palette.color(QPalette.Window).lightness() < 128
    except:
        return False


def apply_auto_theme(app):
    """Applique le thème selon le mode système"""
    if is_dark_mode_system():
        apply_modern_dark_theme(app)
        logger.info("Thème sombre automatique appliqué")
    else:
        apply_modern_light_theme(app)
        logger.info("Thème clair automatique appliqué")


# ====================== FENÊTRE PRINCIPALE ======================
class DocumentationMainWindow:
    """Point d'entrée principal pour le générateur de documentation"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')  # Style moderne cohérent

        # Application du thème
        #apply_modern_light_theme(self.app)      # Light Mode (recommandé ici)
        #apply_modern_dark_theme(self.app)     # dark Mode (optionnel)
        apply_auto_theme(self.app)

        # Icône de l'application (optionnel - à adapter)
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            self.app.setWindowIcon(QIcon(str(icon_path)))
        else:
            logger.warning(f"Icône non trouvée : {icon_path}")

        # Création et affichage du wizard
        self.wizard = SetupWizardDoc()

        # Connexion du signal de fin (optionnel : pour actions post-génération)
        self.wizard.finished.connect(self.on_wizard_finished)

    def run(self):
        """Lance l'interface"""
        logger.info("Lancement de l'interface du Générateur de Documentation")
        self.wizard.show()
        sys.exit(self.app.exec())

    def on_wizard_finished(self, result):
        """Appelé quand le wizard est fermé"""
        if result == QWizard.Accepted:
            logger.info("Wizard terminé avec succès (génération lancée)")
            self.wizard.close()
        else:
            logger.info("Wizard annulé par l'utilisateur")
            self.wizard.close()


# ====================== POINT D'ENTRÉE ======================
if __name__ == "__main__":
    try:
        # Création et exécution de la fenêtre principale
        main_window = DocumentationMainWindow()
        main_window.run()


    except Exception as e:
        logging.critical(f"Erreur critique au démarrage : {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Erreur de démarrage",
            f"Impossible de lancer l'interface de génération de documentation :\n\n{str(e)}"
        )
        sys.exit(1)