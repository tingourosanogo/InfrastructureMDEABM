# src/gaml_generator/generator.py

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound

from ..model_intermediate.structures import SocioEcosystemModel, AgentModel, ProcessModel
from .pseudocodeToaction.gaml_emitter import GamlEmitter, EmissionConfig, EmissionResult

logger = logging.getLogger(__name__)

class GamlGenerator:
    """
    Générateur GAML modulaire avec architecture à fichiers multiples.
    Intégration du pipeline pseudoCode refondu (Lark-based) pour les processus.
    """

    def __init__(self, 
                 model: SocioEcosystemModel, 
                 template_dir: str = "src/gaml_generator/templates",
                 output_dir: str = "output_gaml",
                 modular: bool = True,
                 generate_reflex_default: bool = True):  # Nouveau param pour reflex
        
        self.model = model
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.modular = modular
        self.generate_reflex_default = generate_reflex_default
        
        # Configuration Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['gaml']),
            trim_blocks=True,
            lstrip_blocks=True,
            extensions=['jinja2.ext.do']
        )

        self._register_custom_filters()
        
        # Métadonnées
        self.generation_time = datetime.now()

        # Instance unique de l'Emitter (réutilisée pour tous les processus)
        self.emitter = GamlEmitter(
            logger=logger,
            config=EmissionConfig(
                indent_size=4,
                generate_reflex=generate_reflex_default,
                reflex_suffix="_dynamics",
                include_header_comments=True,
                minify=False
            )
        )

    def _create_output_structure(self):
        """Crée l'arborescence des répertoires de sortie"""
        directories = [
            self.output_dir,
            self.output_dir / "species",
            self.output_dir / "behaviors", 
            self.output_dir / "experiments",
            self.output_dir / "outputs",
            self.output_dir / "resources"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Répertoire créé: {directory}")

    def _register_custom_filters(self):
        """Enregistre les filtres Jinja2 personnalisés pour GAML"""
        
        def sanitize_gaml(value):
            """Nettoie les noms pour être valides en GAML"""
            if not value:
                return "unnamed"
            # Remplacer caractères spéciaux
            cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', str(value))
            # S'assurer que ça commence par une lettre
            if cleaned and cleaned[0].isdigit():
                cleaned = 'var_' + cleaned
            return cleaned.lower()
        
        def default_value(value, default):
            """Retourne une valeur par défaut si None/empty"""
            return value if value is not None and value != "" else default
        
        def gaml_type(value):
            """Infère le type GAML à partir de la valeur"""
            if isinstance(value, bool):
                return "bool"
            elif isinstance(value, int):
                return "int"
            elif isinstance(value, float):
                return "float"
            elif isinstance(value, str):
                return "string"
            elif isinstance(value, list):
                return "list"
            else:
                return "object"
            
        
        def format_comment(text, max_length=80):
            """Formate les commentaires avec longueur limitée"""
            if not text:
                return ""
            words = text.split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= max_length:
                    current_line += (" " if current_line else "") + word
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            return " // " + " \\n// ".join(lines) if lines else ""
        
        # Enregistrement des filtres
        self.env.filters['sanitize_gaml'] = sanitize_gaml
        self.env.filters['default'] = default_value
        self.env.filters['gaml_type'] = gaml_type
        self.env.filters['format_comment'] = format_comment
        
    # Pipeline de génération pour un processus donné
    


    def _prepare_context(self) -> Dict:
        """Prépare le contexte pour les templates Jinja2 avec intégration robuste de l'Emitter"""
        try:
            agents_with_count = [
                agent for agent in self.model.agents.values()
                if agent.initial_count > 0
            ]

            ordered_agents = self._get_agents_in_order()

            for agent in ordered_agents:
                agent.parent_name = self._get_parent_name(agent)
                for attr in agent.attributes:
                    if not hasattr(attr, 'type'):
                        attr.type = 'float'

                # Identification des processus liés à l'agent
                processes_for_agent = [
                    process for process in self.model.processes.values()
                    if agent.id in process.subjects_refs
                ]

                process_gaml_code = ""
                logger.debug(f"Agent {agent.name} (ID: {agent.id}) → {len(processes_for_agent)} processus liés")

                for process in processes_for_agent:
                    if not process.pseudoCode or not process.pseudoCode.strip():
                        logger.warning(f"PseudoCode vide pour le processus {process.name} de l'agent {agent.name}")
                        continue

                    try:
                        # Appel haut-niveau du pipeline complet via l'instance unique
                        emission_result: EmissionResult = self.emitter.generate_from_pseudo_code(
                            process_name=process.name,
                            pseudo_code=process.pseudoCode,
                            equation=process.equation,
                            description=process.description,
                            depends_on=process.involvedResources_refs or []
                        )

                        # Gestion propre des warnings du pipeline
                        if emission_result.warnings:
                            logger.warning(f"Warnings pour {process.name}: {emission_result.warnings}")

                        process_gaml_code += emission_result.code + "\n\n"

                        #print("Code GAML généré :")
                        #print("-" * 90)
                        #print(emission_result.code)
                        #print("-" * 90)

                    except Exception as e:
                        logger.error(f"Erreur génération GAML pour processus {process.name} de {agent.name}: {e}")
                        process_gaml_code += f"// ERREUR pour processus {process.name}: {str(e)}\n\n"
                
                agent.process_gaml_code = process_gaml_code.strip()
            
            # Identification des processus globaux
            global_processes = self._identify_global_processes()

            return {
                "model": self.model,
                "initialization_config": self.model.initialization_config,
                "global_parameters": self.model.global_parameters,
                "agents": ordered_agents,  
                "agents_with_count": agents_with_count,
                "indicators": self.model.indicators,
                "global_processes": global_processes,
                "scenarios": self.model.scenarios,
                "now": self.generation_time
            }
        except Exception as e:
            logger.error(f"Erreur lors de la préparation du contexte : {e}")
            return {}  # Fallback vide

    def _get_parent_name(self, agent: AgentModel) -> str:
        """Retourne le nom du parent d'un agent"""
        if not agent.partOfParentAgent_ref:
            return ""
        
        parent = self.model.get_agent_by_id(agent.partOfParentAgent_ref)
        return parent.name if parent else ""

    def _identify_global_processes(self) -> List[ProcessModel]:
        """Identifie les processus sans sujet spécifique (globaux)"""
        global_processes = []
        for process in self.model.processes.values():
            if not process.subjects_refs and not process.involvedResources_refs:
                global_processes.append(process)
            elif process.name.lower() in ['system_update', 'global_sync', 'environment_update']:
                global_processes.append(process)
        return global_processes

    def _validate_template(self, template_name: str) -> bool:
        """Valide l'existence d'un template"""
        template_path = self.template_dir / template_name
        if not template_path.exists():
            logger.warning(f"Template manquant: {template_name}")
            return False
        return True
    
    

    def generate_monolithic(self) -> Path:
        """Génère un fichier GAML monolithique (ancienne approche)"""
        try:
            logger.info("Génération monolithique du modèle GAML")
            
            context = self._prepare_context()
            output_path = self.output_dir / "model_monolithic.gaml"

            templates_flow = [
                ("header.j2", "header"),
                ("globals.j2", "globals"), 
                ("species.j2", "species"),
                ("reflexes.j2", "reflexes"),
                ("init.j2", "init"),
                ("experiments.j2", "experiments"),
                ("outputs.j2", "outputs")
            ]

            gaml_blocks = []
            
            for template_name, section_name in templates_flow:
                if not self._validate_template(template_name):
                    continue
                    
                try:
                    template = self.env.get_template(template_name)
                    rendered = template.render(**context)
                    
                    if rendered.strip():
                        gaml_blocks.append(f"// === {section_name.upper()} ===\n{rendered.strip()}\n")
                        logger.debug(f"Section '{section_name}' générée avec succès")
                        
                except Exception as e:
                    logger.error(f"Erreur lors du rendu du template {template_name}: {e}")
                    continue

            # Assemblage final
            final_content = "\n".join(gaml_blocks)
            output_path.write_text(final_content, encoding="utf-8")
            
            logger.info(f"Modèle GAML monolithique généré: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Erreur lors de la génération monolithique : {e}")
            return {}

    def generate_modular(self) -> Dict[Path, str]:
        """Génération modulaire CORRIGÉE - un fichier par espèce"""
        try:
            logger.info("Génération modulaire du modèle GAML")
            
            # Préparation du contexte global pour tous les templates
            context = self._prepare_context()
            
            # Création des répertoires de sortie
            self._create_output_structure()

            generated_files = {}

            # 1. Fichier principal
            main_template = "main_modular.j2"
            if self._validate_template(main_template):
                try:
                    template = self.env.get_template(main_template)
                    main_content = template.render(**context)
                    main_path = self.output_dir / "model.gaml"
                    main_path.write_text(main_content, encoding="utf-8")
                    generated_files[main_path] = main_content
                    logger.info(f"Fichier principal généré: {main_path}")
                except Exception as e:
                    logger.error(f"Erreur génération fichier principal: {e}")

            # 2. Modules globaux (inchangé)
            global_modules = [
                ("globals.j2", "globals.gaml"),
                ("reflexes.j2", "behaviors/global_reflexes.gaml"),
                ("outputs.j2", "outputs/indicators.gaml")
            ]
            
            for template_name, output_path in global_modules:
                if self._validate_template(template_name):
                    try:
                        template = self.env.get_template(template_name)
                        content = template.render(**context)
                        file_path = self.output_dir / output_path
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(content, encoding="utf-8")
                        generated_files[file_path] = content
                        logger.debug(f"Module généré: {file_path}")
                    except Exception as e:
                        logger.error(f"Erreur génération module {template_name}: {e}")

            # 3. Fichiers d'espèces INDIVIDUELS
            species_template = "species_single.j2"  # NOUVEAU TEMPLATE
            if self._validate_template(species_template):
                for index, agent in enumerate(context["agents"]):
                    if agent.attributes or getattr(agent, 'process_gaml_code', '').strip():  # Uniquement les espèces avec contenu
                        try:
                            template = self.env.get_template(species_template)
                            # Contexte spécifique à CETTE espèce seulement
                            agent_context = {
                                "agent": agent,
                                "agent_color_r": (index * 50) % 255,
                                "agent_color_g": (index * 100) % 255, 
                                "agent_color_b": (index * 150) % 255
                            }
                            content = template.render(**agent_context)
                            file_path = self.output_dir / "species" / f"{agent.name.lower()}.gaml"
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            file_path.write_text(content, encoding="utf-8")
                            generated_files[file_path] = content
                            logger.debug(f"Espèce générée: {file_path}")
                        except Exception as e:
                            logger.error(f"Erreur génération espèce {agent.name}: {e}")
            else:
                logger.error(f"Template espèces individuelles manquant: {species_template}")

            # 4. Fichiers d'expérimentation
            experiment_template = "experiments.j2"
            if self._validate_template(experiment_template):
                try:
                    template = self.env.get_template(experiment_template)
                    content = template.render(**context)
                    file_path = self.output_dir / "experiments" / "main_experiment.gaml"
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding="utf-8")
                    generated_files[file_path] = content
                    logger.debug(f"Expérimentation générée: {file_path}")
                except Exception as e:
                    logger.error(f"Erreur génération expérimentation: {e}")

            logger.info(f"Structure modulaire générée: {len(generated_files)} fichiers créés")
            return generated_files
        except Exception as e:
            logger.error(f"Erreur lors de la génération modulaire: {e}")
            return {}

    def generate(self, output_dir: str, modular: Optional[bool] = None) -> Path:
        """
        Point d'entrée principal pour la génération GAML
        
        Args:
            output_dir: Repertoire du fichier de sortie (pour mode monolithique)
            modular: True pour génération modulaire, False pour monolithique
            
        Returns:
            Chemin vers le fichier principal généré
        """
        # Utilise le mode spécifié ou celui par défaut
        use_modular = modular if modular is not None else self.modular
        
        if use_modular:
            generated_files = self.generate_modular()
            # Retourne le chemin du fichier principal
            main_file = self.output_dir / "model.gaml"
            return main_file if main_file in generated_files else next(iter(generated_files.keys()))
        else:
            return self.generate_monolithic()

    def validate_generation(self) -> Tuple[bool, List[str]]:
        """
        Valide la génération effectuée
        
        Returns:
            Tuple (succès, liste des messages d'erreur)
        """
        errors = []
        
        # Vérification des agents
        if not self.model.agents:
            errors.append("Aucun agent dans le modèle - génération impossible")
        
        # Vérification des templates essentiels
        essential_templates = ["main_modular.j2" if self.modular else "header.j2", "species.j2"]
        for template in essential_templates:
            if not self._validate_template(template):
                errors.append(f"Template essentiel manquant: {template}")
        
        agents_with_process = set()
        for process in self.model.processes.values():
            agents_with_process.update(process.subjects_refs)
            
        # 2. Vérification de la cohérence des données
        for agent in self.model.agents.values():
            # Un agent est considéré comme "vide" s'il n'a NI attributs NI processus assigné
            if not agent.attributes and agent.id not in agents_with_process: 
                logger.warning(f"Agent '{agent.name}' sans attributs ni processus assignés (vide conceptuellement)")
        
        for process in self.model.processes.values():
            if not process.pseudoCode.strip():
                errors.append(f"PseudoCode vide pour processus {process.name}")
        return len(errors) == 0, errors

    
    def get_generation_report(self) -> Dict:
        """Génère un rapport détaillé de la génération"""
        context = self._prepare_context()
        
        return {
            "timestamp": self.generation_time.isoformat(),
            "model_name": self.model.initialization_config.get('metadata', {}).get('model_name', 'Unknown'),
            "agents_count": len(self.model.agents),
            "agents_with_initial_count": len([a for a in self.model.agents.values() if a.initial_count > 0]),
            "properties_count": len(self.model.properties),
            "processes_count": len(self.model.processes),
            "indicators_count": len(self.model.indicators),
            "global_parameters_count": len(self.model.global_parameters),
            "generation_mode": "modular" if self.modular else "monolithic",
            "output_directory": str(self.output_dir)
        }
    

    # Ajoutez cette méthode à votre GamlGenerator
    def _get_agents_in_order(self):
        """Retourne les agents dans l'ordre topologique (parents d'abord)"""
        agents = list(self.model.agents.values())
        
        # Préparer les noms de parents
        for agent in agents:
            agent.parent_name = self._get_parent_name(agent)
        
        # Séparer les agents avec et sans parent
        root_agents = [a for a in agents if not a.parent_name or a.parent_name == ""]
        child_agents = [a for a in agents if a.parent_name and a.parent_name != ""]
        
        # Ordonner récursivement
        ordered_agents = root_agents.copy()
        
        # Ajouter les enfants après leurs parents
        max_iterations = len(agents) * 2
        for iteration in range(max_iterations):
            added_any = False
            remaining_children = []
            
            for agent in child_agents:
                # Vérifier si le parent est déjà dans la liste ordonnée
                parent_in_list = any(ordered_agent.name == agent.parent_name for ordered_agent in ordered_agents)
                
                if parent_in_list:
                    ordered_agents.append(agent)
                    added_any = True
                else:
                    remaining_children.append(agent)
            
            child_agents = remaining_children
            
            # Arrêter si plus d'ajouts possibles ou liste vide
            if not added_any or not child_agents:
                break
        
        # Ajouter les agents restants (au cas où il y aurait des références circulaires)
        if child_agents:
            logger.warning(f"Agents non ordonnés (références circulaires?): {[a.name for a in child_agents]}")
            ordered_agents.extend(child_agents)
        
        logger.info(f"Ordre topologique établi: {[a.name for a in ordered_agents]}")
        return ordered_agents
    
