from typing import Dict, List, Optional
from .base import BaseSection
import logging
import textwrap

logger = logging.getLogger(__name__)

class IntroductionSection(BaseSection):
    """Génère la section 'Introduction' à partir du JSON structuré"""
    
    # Constantes de formatage
    DEFAULT_MESSAGE = "*Information à compléter*"
    EMPTY_SECTION = "*Section en cours de rédaction*"
    
    def generate(self) -> str:
        """Point d'entrée principal avec gestion d'erreurs"""
        try:
            if not self._has_valid_data():
                return self._format_main_title("Introduction", self.EMPTY_SECTION)
            
            content = [
                # self._build_header(),
                self._build_principles_section(),
                self._build_model_section(),
                self._build_context_section(),
                # self._build_references_section()
            ]
            
            return self._format_main_title("Introduction", "\n\n".join(filter(None, content)))
            
        except Exception as e:
            logger.error(f"ERREUR GENERATION INTRODUCTION: {str(e)}")
            return self._format_main_title("Introduction", self.EMPTY_SECTION)

    def _has_valid_data(self) -> bool:
        """Valide la structure minimale des données"""
        return isinstance(self.data, dict) and any(
            key in self.data for key in ['principe_modelisation', 'modele_specifique']
        )

    def _format_main_title(self, title: str, content: str) -> str:
        """Formatte le titre principal"""
        return f"# {title}\n\n{content.strip()}"

    def _build_header(self) -> str:
        """En-tête avec métadonnées"""
        metadata = self.data.get('metadata', {})
        return f"""**Auteur** : {metadata.get('auteur', self.DEFAULT_MESSAGE)}  
**Rédigé le** : {metadata.get('date_creation', self.DEFAULT_MESSAGE)}  
**Référence du modèle** : {metadata.get('modele_reference', self.DEFAULT_MESSAGE)}"""

    def _build_principles_section(self) -> str:
        """Section Principes de modélisation"""
        principles = self.data.get('principe_modelisation', {})
        if not principles:
            return None
            
        content = ["## Principe et définitions"]
        
        # Question de recherche
        question = principles.get('question_recherche', {})
        if question:
            content.append(self._build_research_question(question))
        
        # Concepts fondamentaux
        concepts = principles.get('concepts_fondamentaux', {})
        if concepts:
            content.append(self._build_fundamental_concepts(concepts))
        
        # Relations questions-modèle
        relations = principles.get('relation_questions_modele', {})
        if relations:
            content.append(self._build_model_relations(relations))
        
        return "\n\n".join(content)

    def _build_research_question(self, question: Dict) -> str:
        """Construction de la question de recherche"""
        content = [
            "Toute modélisation part d'une question de la forme :",
            f"\n**{question.get('formulation', self.DEFAULT_MESSAGE)}**",
            "",
            "dans laquelle :"
        ]
        
        explication = question.get('explication', '').strip()
        if explication:
            # Extraction des points de la explication
            lines = explication.split('\n')
            for line in lines:
                if line.strip() and '- ' in line:
                    content.append(f"\n{line}")
        
        return "\n".join(content)

    def _build_fundamental_concepts(self, concepts: Dict) -> str:
        """Construction des concepts fondamentaux"""
        content = ["### Concepts fondamentaux"]
        
        # Entités
        entites = concepts.get('entites', '')
        if entites:
            content.append(f"- **Système** : {entites}")
        
        # Attributs
        attributs = concepts.get('attributs', [])
        if attributs:
            content.append("\n**Types d'attributs** :")
            for attr in attributs:
                content.append(f" \n - **{attr.get('type', '?')}** : {attr.get('definition', self.DEFAULT_MESSAGE)}")
        
        # Portée des attributs
        portee = concepts.get('portee_attributs', [])
        if portee:
            content.append("\n**Portée des attributs** :")
            for scope in portee:
                content.append(f" \n - {scope}")
        
        return "\n".join(content)

    def _build_model_relations(self, relations: Dict) -> str:
        """Relations entre questions et modèle"""
        content = ["### Relations questions-modèle"]
        
        explication = relations.get('explication', '')
        if explication:
            content.append("**Formalisation** :")
            # Formatage des équations/relations
            lines = explication.split('\n')
            for line in lines:
                if line.strip():
                    content.append(f"```\n{line.strip()}\n```")
        
        implication = relations.get('implication', '')
        if implication:
            content.append(f"\n**Implication** : {implication}")
        
        return "\n".join(content)

    def _build_model_section(self) -> str:
        """Section Modèle spécifique"""
        modele = self.data.get('modele_specifique', {})
        if not modele:
            return None
            
        content = ["## Le modèle"]
        
        # Question centrale
        question = modele.get('question_centrale', {})
        if question:
            content.append(self._build_central_question(question))
        
        # Diagrammes
        diagrammes = modele.get('diagrammes', [])
        if diagrammes:
            content.append(self._build_diagrams(diagrammes))
        
        # Composants principaux
        composants = modele.get('composants_principaux', [])
        if composants:
            content.append(self._build_components(composants))
        
        # Acteurs
        acteurs = modele.get('acteurs', [])
        if acteurs:
            content.append(self._build_actors(acteurs))
        
        return "\n\n".join(content)

    def _build_central_question(self, question: Dict) -> str:
        """Question centrale du modèle"""
        content = [
            "La question retenue pour le modèle est :",
            f"\n**{question.get('formulation', self.DEFAULT_MESSAGE)}**",
            "",
            f"\n**Domaine** : {question.get('domaine', self.DEFAULT_MESSAGE)}",
            f"\n**Échelle** : {question.get('echelle', self.DEFAULT_MESSAGE)}"
        ]
        return "\n".join(content)

    def _build_diagrams(self, diagrammes: List[Dict]) -> str:
        """Construction des diagrammes avec légendes"""
        content = ["### Représentations graphiques"]
        
        for i, diagram in enumerate(diagrammes, 1):
            diagram_content = [
                f"![]({diagram.get('fichier', '')})",
                f"\n**Figure {i}** : {diagram.get('legende', '')}",
                "",
                diagram.get('description', self.DEFAULT_MESSAGE)
            ]
            content.append("\n".join(diagram_content))
            if i < len(diagrammes):
                content.append("")  # Espace entre diagrammes
        
        return "\n".join(content)

    def _build_components(self, composants: List[Dict]) -> str:
        """Composants principaux du modèle"""
        content = ["### Composants principaux"]
        
        for composant in composants:
            comp_content = [f"#### {composant.get('nom', 'Composant').title()}"]
            comp_content.append(f"**Description** : {composant.get('description', self.DEFAULT_MESSAGE)}")
            
            role = composant.get('role')
            if role:
                comp_content.append(f"\n**Rôle** : {role}")
            
            types = composant.get('types', [])
            if types:
                comp_content.append("\n**Types** :")
                comp_content.extend(f"\n- {t}" for t in types)
            
            usages = composant.get('usages', [])
            if usages:
                comp_content.append("\n**Usages** :")
                comp_content.extend(f"\n- {u}" for u in usages)
            
            content.append("\n".join(comp_content))
        
        return "\n\n".join(content)

    def _build_actors(self, acteurs: List[Dict]) -> str:
        """Acteurs du système"""
        content = ["### Acteurs du système"]
        
        for acteur in acteurs:
            content.append(
                f"- **{acteur.get('type', 'Acteur').title()}** : "
                f"{acteur.get('exemple', self.DEFAULT_MESSAGE)}"
            )
        
        return "\n".join(content)

    def _build_context_section(self) -> str:
        """Section Contextualisation"""
        context = self.data.get('contextualisation', {})
        if not context:
            return None
            
        content = ["## Contextualisation"]
        
        domaine = context.get('domaine_application', '')
        if domaine:
            content.append(f"**Domaine d'application** : {domaine}")
        
        pertinence = context.get('pertinence_scientifique', '')
        if pertinence:
            content.append(f"\n**Pertinence scientifique** : {pertinence.strip()}")
        
        public = context.get('public_cible', [])
        if public:
            content.append("\n**Public cible** :")
            content.extend(f"- {p}" for p in public)
        
        return "\n".join(content)

    def _build_references_section(self) -> str:
        """Section Références bibliographiques"""
        references = self.data.get('references_bibliographiques', [])
        if not references:
            return None
            
        content = ["## Références bibliographiques"]
        
        for ref in references:
            ref_content = [
                f"- **{ref.get('auteur', 'Auteur inconnu')}** ({ref.get('annee', 'N.D.')})",
                f"  {ref.get('titre', 'Titre manquant')}"
            ]
            
            journal = ref.get('journal')
            edition = ref.get('edition')
            if journal:
                ref_content.append(f"  *{journal}*")
            elif edition:
                ref_content.append(f"  {edition}")
            
            content.append("\n".join(ref_content))
        
        return "\n\n".join(content)