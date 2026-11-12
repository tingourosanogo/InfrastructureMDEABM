from typing import Dict, List, Optional
from .base import BaseSection
import logging
import textwrap

logger = logging.getLogger(__name__)

class UserManualSection(BaseSection):
    """Génère la section 'Mode d'emploi' à partir du JSON structuré"""
    
    # Constantes de formatage
    DEFAULT_MESSAGE = "*Information à compléter*"
    EMPTY_SECTION = "*Section en cours de rédaction*"
    
    def generate(self) -> str:
        """Point d'entrée principal avec gestion d'erreurs"""
        try:
            if not self._has_valid_data():
                return self._format_main_section("Mode d'emploi", self.EMPTY_SECTION)
            
            content = [
                #self._build_header(),
                self._build_launch_section(),
                self._build_inputs_section(),
                self._build_outputs_section()
            ]
            
            return self._format_main_section("Mode d'emploi", "\n\n".join(filter(None, content)))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION MODE D'EMPLOI: {str(e)}")
            return self._format_main_section("Mode d'emploi", self.EMPTY_SECTION)

    def _has_valid_data(self) -> bool:
        """Valide la structure minimale des données"""
        return isinstance(self.data, dict) and any(
            key in self.data for key in ['lancement_simulation', 'entrees', 'sorties']
        )

    def _format_main_section(self, title: str, content: str) -> str:
        """Formatte une section principale"""
        return f"# {title}\n\n{content.strip()}"

    def _build_header(self) -> str:
        """En-tête avec métadonnées"""
        metadata = self.data.get('metadata', {})
        return f"""**Auteur** : {metadata.get('auteur', self.DEFAULT_MESSAGE)}  
**Version du modèle** : {metadata.get('version_modele', self.DEFAULT_MESSAGE)}  
**Dernière mise à jour** : {metadata.get('date_mise_a_jour', self.DEFAULT_MESSAGE)}"""

    def _build_launch_section(self) -> str:
        """Section Lancement de la simulation"""
        launch_data = self.data.get('lancement_simulation', {})
        if not launch_data:
            return None
            
        content = ["## Lancement de la simulation"]
        
        # Plateforme requise
        platform = launch_data.get('plateforme_requise', {})
        if platform:
            content.append("### Configuration requise")
            content.append(self._build_platform_table(platform))
        
        # Fichiers nécessaires
        fichiers = launch_data.get('fichiers_necessaires', [])
        if fichiers:
            content.append("### Fichiers nécessaires")
            content.append(self._build_files_table(fichiers))
        
        # Procédure
        procedure = launch_data.get('procedure', [])
        if procedure:
            content.append("### Procédure de lancement")
            content.append(self._build_procedure_steps(procedure))
        
        return "\n\n".join(content)

    def _build_platform_table(self, platform: Dict) -> str:
        """Table de configuration requise"""

        rows = [
            f"| **Système d'exploitation** | {', '.join(platform.get('os', []))} |",
            f"| **Mémoire RAM** | {platform.get('memoire_ram', self.DEFAULT_MESSAGE)} |",
            f"| **Espace disque** | {platform.get('espace_disque', self.DEFAULT_MESSAGE)} |",
            f"| **Dépendances** | {', '.join(platform.get('dependances', []))} |"
        ]
        return "| | |\n| - | - |\n" + "\n".join(rows)
    

    def _build_files_table(self, fichiers: List[Dict]) -> str:
        """Table des fichiers nécessaires"""
        headers = "| **Fichier** | **Description** | **Format** | **Exemple** |\n| - | - | - | - |"
        rows = []
        
        for fichier in fichiers:
            rows.append(
                f"| `{fichier.get('nom', '?')}` | "
                f"{fichier.get('description', self.DEFAULT_MESSAGE)} | "
                f"{fichier.get('format', '?')} | "
                f"`{fichier.get('exemple', 'N/A')}` |"
            )
        
        return headers + "\n" + "\n".join(rows)

    def _build_procedure_steps(self, procedure: List[Dict]) -> str:
        """Étapes de procédure avec commandes"""
        content = []
        for step in procedure:
            step_content = [
                f"**Étape {step['etape']}** : {step.get('description', self.DEFAULT_MESSAGE)}",
                f"```bash\n{step.get('commande', '# Commande manquante')}\n```"
            ]
            
            if step.get('options'):
                step_content.append("**Options disponibles** :")
                step_content.extend(f"- {opt}" for opt in step['options'])
            
            if step.get('prerequis'):
                step_content.append(f"**Prérequis** : {step['prerequis']}")
            
            content.append("\n".join(step_content))
        
        return "\n\n".join(content)

    def _build_inputs_section(self) -> str:
        """Section Entrées"""
        entrees = self.data.get('entrees', {})
        if not entrees:
            return None
            
        content = ["## Les entrées"]
        
        # Interface utilisateur
        interface = entrees.get('interface_utilisateur', {})
        if interface and interface.get('disponible', False):
            content.append("### Interface utilisateur")
            content.append(self._build_interface_table(interface))
        
        # Fichiers d'entrée
        fichiers = entrees.get('fichiers_entree', [])
        if fichiers:
            content.append("### Fichiers d'entrée")
            content.append(self._build_input_files_table(fichiers))
        
        return "\n\n".join(content)

    def _build_interface_table(self, interface: Dict) -> str:
        """Table de l'interface utilisateur"""
        rows = [
            f"| **Type** | {interface.get('type', self.DEFAULT_MESSAGE)} |",
            f"| **URL** | `{interface.get('url', self.DEFAULT_MESSAGE)}` |",
            f"| **Fonctionnalités** | {', '.join(interface.get('fonctionnalites', []))} |"
        ]
        return "| | |\n| - | - |\n" + "\n".join(rows)

    def _build_input_files_table(self, fichiers: List[Dict]) -> str:
        """Table des fichiers d'entrée"""
        headers = "| **Type** | **Description** | **Format** | **Détails** |\n| - | - | - | - |"
        rows = []
        
        for fichier in fichiers:
            details = []
            if fichier.get('champs_obligatoires'):
                details.append(f"Champs obligatoires: {', '.join(fichier['champs_obligatoires'])}")
            if fichier.get('systeme_coordonnees'):
                details.append(f"Système: {fichier['systeme_coordonnees']}")
            if fichier.get('schema'):
                details.append(f"Schéma: {fichier['schema']}")
            
            rows.append(
                f"| {fichier.get('type', '?')} | "
                f"{fichier.get('description', self.DEFAULT_MESSAGE)} | "
                f"{fichier.get('format', '?')} | "
                f"{'; '.join(details) if details else 'Aucun'} |"
            )
        
        return headers + "\n" + "\n".join(rows)

    def _build_outputs_section(self) -> str:
        """Section Sorties"""
        sorties = self.data.get('sorties', {})
        if not sorties:
            return None
            
        content = ["## Les sorties"]
        
        # Visualisation
        visualisations = sorties.get('visualisation', [])
        if visualisations:
            content.append("### Visualisation")
            content.append(self._build_visualization_table(visualisations))
        
        # Fichiers de sortie
        fichiers = sorties.get('fichiers_sortie', [])
        if fichiers:
            content.append("### Fichiers de sortie")
            content.append(self._build_output_files_table(fichiers))
        
        # Post-traitement
        post_traitement = sorties.get('post_traitement', {})
        if post_traitement:
            content.append("### Post-traitement")
            content.append(self._build_post_processing(post_traitement))
        
        return "\n\n".join(content)

    def _build_visualization_table(self, visualisations: List[Dict]) -> str:
        """Table des visualisations"""
        headers = "| **Type** | **Description** | **Format** | **Outils** |\n| - | - | - | - |"
        rows = []
        
        for viz in visualisations:
            rows.append(
                f"| {viz.get('type', '?')} | "
                f"{viz.get('description', self.DEFAULT_MESSAGE)} | "
                f"{viz.get('format', '?')} | "
                f"{viz.get('outils', '?')} |"
            )
        
        return headers + "\n" + "\n".join(rows)

    def _build_output_files_table(self, fichiers: List[Dict]) -> str:
        """Table des fichiers de sortie"""
        headers = "| **Type** | **Description** | **Format** | **Contenu** |\n| - | - | - | - |"
        rows = []
        
        for fichier in fichiers:
            contenu = []
            if fichier.get('colonnes'):
                contenu.append(f"Colonnes: {', '.join(fichier['colonnes'])}")
            if fichier.get('sections'):
                contenu.append(f"Sections: {', '.join(fichier['sections'])}")
            
            rows.append(
                f"| {fichier.get('type', '?')} | "
                f"{fichier.get('description', self.DEFAULT_MESSAGE)} | "
                f"{fichier.get('format', '?')} | "
                f"{'; '.join(contenu) if contenu else 'Données structurées'} |"
            )
        
        return headers + "\n" + "\n".join(rows)

    def _build_post_processing(self, post_traitement: Dict) -> str:
        """Section post-traitement"""
        content = []
        
        if post_traitement.get('outils_recommandes'):
            content.append("**Outils recommandés** :")
            content.extend(f"- {outil}" for outil in post_traitement['outils_recommandes'])
        
        if post_traitement.get('scripts_exemples'):
            content.append(f"\n**Scripts d'exemple** : `{post_traitement['scripts_exemples']}`")
        
        return "\n".join(content) if content else None