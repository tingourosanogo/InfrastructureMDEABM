from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from .base import BaseSection
import logging
import json

logger = logging.getLogger(__name__)

class CoverPageSection(BaseSection):
    """Génère la page de garde professionnelle à partir de la configuration"""
    
    def generate(self) -> str:
        """Génère la page de garde complète"""
        try:
            if not self._has_valid_config():
                return self._generate_minimal_cover()
            
            content = [
                self._generate_header(),
                self._generate_title_section(),
                self._generate_authors_section(),
                self._generate_project_info(),
                self._generate_metadata_section(),
                self._generate_footer(),
                self._generate_tableOfContent()
            ]
            
            return "\n\n".join(filter(None, content))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION PAGE DE GARDE: {str(e)}")
            return self._generate_minimal_cover()

    def _has_valid_config(self) -> bool:
        """Valide la présence des champs essentiels"""
        return bool(self.data.get('metadata', {}).get('title'))

    def _generate_minimal_cover(self) -> str:
        """Page de garde minimaliste en cas d'erreur"""
        return f"""# Page de garde - Configuration incomplète

**Généré le** : {datetime.now().strftime('%d/%m/%Y')}
"""

    from pathlib import Path

    def _generate_header(self) -> str:
        """En-tête avec logo et information"""
        header_lines = []
        
        logo_path_str = self.data.get('assets', {}).get('logo')
        
        header_lines.append("---")
        if logo_path_str:
            logo_path = Path(logo_path_str)
            
            if logo_path.exists() and logo_path.is_file():
                header_lines.append(f"![]({logo_path.as_posix()})\n")
                #header_lines.append("---")

        return "\n".join(header_lines) if header_lines else ""


    def _generate_title_section(self) -> str:
        """Section titre et sous-titre"""
        metadata = self.data.get('metadata', {})
        
        title = metadata.get('title', 'Document de spécification')
        subtitle = metadata.get('subtitle', '')
        version = metadata.get('version', '1.0.0')
        
        content = [f"# {title}"]
        
        if subtitle:
            content.append(f"### {subtitle}")
        
        content.append(f"**Version** : {version}")
        
        # Dates importantes
        date_version = metadata.get('date_version', datetime.now().strftime('%Y-%m-%d'))
        content.append(f"**Date de version** : {self._format_date(date_version)}")
        
        status = metadata.get('status', 'Brouillon')
        classification = metadata.get('classification', 'Interne')
        #content.append(f"**Statut** : {status} | **Classification** : {classification}")
        
        return "\n\n".join(content)

    def _generate_authors_section(self) -> str:
        """Section auteurs avec affiliations"""
        authors = self.data.get('authors', [])
        if not authors:
            return None
        
        content = ["## Auteurs"]
        
        for author in authors:
            author_content = [
                f"### {author.get('name', 'Auteur')}",
                #f"**Affiliation** : {author.get('affiliation', 'Non spécifiée')}"
                f"\n**Affiliation** : {author.get('affiliation', '')}"
            ]
            
            if author.get('role'):
                #author_content.append(f"**Rôle** : {author['role']}")
                author_content.append(f"\n**Rôle** : {author.get('role', '')}")
            
            if author.get('email'):
                author_content.append(f"\n**Email** : `{author.get('email', '')}`")
            
            #if author.get('orcid'):
            #     author_content.append(f"**ORCID** : [{author['orcid']}](https://orcid.org/{author['orcid']})")
            
            content.append("\n".join(author_content))
        
        return "\n\n".join(content)

    def _generate_project_info(self) -> str:
        """Information sur le projet"""
        project = self.data.get('project', {})
        if not project:
            return None
        
        content = ["## Information Projet"]
        
        info_lines = []
        if project.get('name'):
            info_lines.append(f"**Nom** : {project['name']}")
        if project.get('acronym'):
            info_lines.append(f"**Acronyme** : {project['acronym']}")
        if project.get('funding'):
            info_lines.append(f"**Financement** : {project['funding']}")
        if project.get('grant_number'):
            info_lines.append(f"**N° Subvention** : {project['grant_number']}")
        if project.get('duration'):
            info_lines.append(f"**Durée** : {project['duration']}")
        if project.get('website'):
            info_lines.append(f"**Site web** : [{project['website']}]({project['website']})")
        if project.get('repository'):
            info_lines.append(f"**Dépôt** : [{project['repository']}]({project['repository']})")
        
        content.append("\n".join(info_lines))
        return "\n\n".join(content)

    def _generate_metadata_section(self) -> str:
        """Métadonnées techniques et documentaires"""
        
        metadata = self.data.get('metadata', {})
        technical = self.data.get('technical', {})
        documentation = self.data.get('documentation', {})
        
        content = ["## Métadonnées"]
        
        # Métadonnées documentaires
        doc_info = []
        if documentation.get('type'):
            doc_info.append(f"**Type** : {documentation['type']}")
        if documentation.get('purpose'):
            doc_info.append(f"**Objectif** : {documentation['purpose']}")
        if documentation.get('audience'):
            doc_info.append(f"**Public cible** : {documentation['audience']}")
        if documentation.get('conformance'):
            doc_info.append(f"**Conformité** : {documentation['conformance']}")
        if documentation.get('license'):
            doc_info.append(f"**Licence** : {documentation['license']}")
        
        if doc_info:
            content.append("### Documentation\n" + "\n".join(doc_info))
        
        # Métadonnées techniques
        tech_info = []
        if technical.get('model_version'):
            tech_info.append(f"**Version modèle** : {technical['model_version']}")
        if technical.get('platform'):
            tech_info.append(f"**Plateforme** : {technical['platform']}")
        if technical.get('programming_language'):
            tech_info.append(f"**Langage** : {technical['programming_language']}")
        if technical.get('minimum_ram'):
            tech_info.append(f"**RAM minimale** : {technical['minimum_ram']}")
        if technical.get('recommended_ram'):
            tech_info.append(f"**RAM recommandée** : {technical['recommended_ram']}")
        if technical.get('dependencies'):
            tech_info.append(f"**Dépendances** : {', '.join(technical['dependencies'])}")
        if technical.get('data_formats'):
            tech_info.append(f"**Formats données** : {', '.join(technical['data_formats'])}")
        
        if tech_info:
            content.append("### Technique\n" + "\n".join(tech_info))
        

        # Mots-clés
        if metadata.get('keywords'):
            content.append(f"**Mots-clés** : {', '.join(f'`{kw}`' for kw in metadata['keywords'])}")
        
        # Langue
        
        if metadata.get('language'):
            content.append(f"**Langue** : {metadata['language'].upper()}")
        
        return "\n\n".join(content)

    def _generate_tableOfContent(self) -> str:
        content= [
            f"## Table des Matières"
            f"\n1. [Introduction](#introduction)"
            f"\n2. [Structure et dynamiques](#structure-et-dynamiques)"
            f"\n3. [Initialisation](#initialisation)"            
            f"\n4. [Indicateurs](#indicateurs)"
            f"\n5. [Mode d'Emploi](#mode-demploi)"
        ]
        return "\n\n".join(content)

    def _generate_footer(self) -> str:
        """Pied de page avec information de génération"""
        footer = [
            "---",
            f"*Document généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*",
            #f"*Système de documentation : CIM-PIM Transformation v1.0*"
        ]
        
        # Image de couverture si disponible
        cover_path = self.data.get('assets', {}).get('cover')
        if cover_path and Path(cover_path).exists():
            footer.insert(0, f"![]({cover_path})")
        
        return "\n".join(footer)

    def _format_date(self, date_str: str) -> str:
        """Formate une date en français"""
        try:
            if '-' in date_str:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.strftime('%d/%m/%Y')
            return date_str
        except ValueError:
            return date_str

