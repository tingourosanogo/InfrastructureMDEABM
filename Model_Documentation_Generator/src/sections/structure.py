from typing import Dict, List, Optional
from .base import BaseSection
import logging
import textwrap

logger = logging.getLogger(__name__)

class StructureSection(BaseSection):
    """Génère la documentation structurelle centrée sur les Agents, conforme au DSL (SocioEcosystem)."""

    DEFAULT_DESC = "*Description à compléter*"
    MISSING_DATA = "..."
    EMPTY_SECTION = "*Section vide : à compléter manuellement*"
    MISSING_DATA_MESSAGE = "*A compléter*"

    def generate(self) -> str:
        """Point d'entrée principal: contre-signe la structure agent → ressources → processus."""
        try:
            if not self._has_valid_data():
                return self._format_main_section("Structure et dynamiques", "Aucune donnée DSL valide trouvée")

            # Ecosystem (en tête facultatif)
            ecosystem_md = self._build_ecosystem(self.data.get("ecosystem", {}))

            # Index pour résolutions rapides
            resources_by_id = self._index_by_id(self.data["entities"].get("resources", []))
            parameters_by_id = self._index_by_id(self.data["entities"].get("parameters", []))
            processes_by_id = self._index_by_id(self.data.get("processes", []))

            # Construire les sections par agent
            agents = self.data["entities"].get("agents", [])
            agents_content = []
            for agent in agents:
                try:
                    # Enrichir l'agent avec ses ressources et ses processus
                    agent_resources = self._collect_agent_resources(agent, resources_by_id)
                    agent_processes = self._collect_agent_processes(agent, processes_by_id)

                    entity_payload = {
                        "id": agent.get("id"),
                        "name": agent.get("name", "Sans nom"),
                        "description": agent.get("description", ""),
                        "comment": agent.get("comment", ""),
                        "type": agent.get("type", self.MISSING_DATA),
                        "attributes": self._adapt_resources_to_attributes(agent_resources),  # pour réutiliser la section attributs
                        "processes": [self._adapt_process_view(p, resources_by_id, parameters_by_id) for p in agent_processes]
                    }

                    entity_md = self._build_entity(entity_payload)
                    agents_content.append(entity_md)
                except Exception as e:
                    logger.error(f"ERREUR GENERATION AGENT {agent.get('name')}: {str(e)}")
                    agents_content.append(f"<!-- Erreur génération agent -->")

            content = "\n\n".join([ecosystem_md] + agents_content if ecosystem_md else agents_content)
            if not content.strip():
                return self._format_main_section("Structure et dynamiques", "Aucun agent valide à documenter")

            return self._format_main_section("Structure et dynamiques", content)

        except Exception as e:
            logger.critical(f"Erreur critique: {str(e)}")
            return self._format_main_section("Structure", "Erreur de génération de la section")

    def _has_valid_data(self) -> bool:
        """Valide la présence des données minimales (centré DSL)."""
        ents = self.data.get("entities")
        return isinstance(ents, dict) and isinstance(ents.get("agents", []), list)

    def _format_main_section(self, title: str, content: str) -> str:
        return f"# {title}\n\n{content.strip()}"

    # ---------- Ecosystem header ----------
    def _build_ecosystem(self, ecosystem: Dict) -> str:
        if not ecosystem:
            return ""
        name = ecosystem.get("name", self.MISSING_DATA)
        location = ecosystem.get("location", self.MISSING_DATA)
        #return f"## 🌍 Ecosystem\n- **Name**: {name}\n- **Location**: {location}" # affiche l'icone
        return f"## Ecosystem\n- **Name**: {name}\n- **Location**: {location}"

    # ---------- Utilities for indexing and resolution ----------
    def _index_by_id(self, items: List[Dict]) -> Dict[str, Dict]:
        idx = {}
        for it in items:
            _id = it.get("id")
            if _id:
                idx[_id] = it
        return idx

    def _resolve_ref(self, ref: Optional[Dict]) -> Optional[str]:
        if not ref:
            return None
        return ref.get("id") or ref.get("name")

    # ---------- Collect resources under agent ----------
    def _collect_agent_resources(self, agent: Dict, resources_by_id: Dict[str, Dict]) -> List[Dict]:
        # 1) via holdsResources href list resolved by parser
        direct_holds = agent.get("holdsResources", [])
        res = []
        for ref in direct_holds:
            rid = self._resolve_ref(ref)
            if rid and rid in resources_by_id:
                res.append(resources_by_id[rid])

        # 2) fallback via inverse relation (Resource.heldBy includes this agent)
        # (utile si certains parsers ne remplissent pas holdsResources côté agent)
        if not res:
            for r in resources_by_id.values():
                held_by_refs = r.get("heldBy", [])
                if any(self._resolve_ref(hb) == agent.get("id") for hb in held_by_refs):
                    res.append(r)
        return res

    # ---------- Collect processes where agent is subject ----------
    def _collect_agent_processes(self, agent: Dict, processes_by_id: Dict[str, Dict]) -> List[Dict]:
        # 1) via isSubjectOf references on agent
        subject_refs = agent.get("isSubjectOf", [])
        procs = []
        if subject_refs:
            for ref in subject_refs:
                pid = self._resolve_ref(ref)
                if pid and pid in processes_by_id:
                    procs.append(processes_by_id[pid])

        # 2) fallback: filter all processes where agent id appears in subjects
        if not procs:
            aid = agent.get("id")
            for p in processes_by_id.values():
                subj = p.get("subjects", [])
                if any(self._resolve_ref(s) == aid for s in subj):
                    procs.append(p)
        return procs

    # ---------- Adapt resources to "attributes" table API ----------
    def _adapt_resources_to_attributes(self, resources: List[Dict]) -> List[Dict]:
        """Remappe les ressources DSL vers le format attendu par la section attributs existante."""
        out = []
        for r in resources:
            out.append({
                "name": r.get("name", self.MISSING_DATA),
                "description": r.get("description", r.get("comment", self.MISSING_DATA)),
                "type": r.get("unit", self.MISSING_DATA)
            })
        return out

    # ---------- Process view adaptation for tables ----------
    def _adapt_process_view(self, process: Dict, resources_by_id: Dict[str, Dict], parameters_by_id: Dict[str, Dict]) -> Dict:
        # Resolve involved resources (inputs)
        involved = []
        for ref in process.get("involvedResources", []):
            rid = self._resolve_ref(ref)
            r = resources_by_id.get(rid) if rid else None
            # Determine entity/owner names from resource.heldBy (may be refs or full dicts)
            held_by = (r or {}).get("heldBy", [])
            if held_by:
                owners = []
                for hb in held_by:
                    if isinstance(hb, dict):
                        owners.append(hb.get("name") or hb.get("id") or self.MISSING_DATA)
                    else:
                        owners.append(hb or self.MISSING_DATA)
                entity_name = ", ".join(owners)
            else:
                entity_name = self.MISSING_DATA

            involved.append({
                "name": (r or {}).get("name", rid or self.MISSING_DATA),
                "entity": entity_name,
                "definition": (r or {}).get("description", (r or {}).get("comment", self.MISSING_DATA)),
                "unit": (r or {}).get("unit", self.MISSING_DATA)
            })

        # Resolve affected resources (outputs)
        affected = []
        for ref in process.get("affectsResources", []):
            rid = self._resolve_ref(ref)
            r = resources_by_id.get(rid) if rid else None
            # Determine entity/owner names from resource.heldBy (may be refs or full dicts)
            held_by = (r or {}).get("heldBy", [])
            if held_by:
                owners = []
                for hb in held_by:
                    if isinstance(hb, dict):
                        owners.append(hb.get("name") or hb.get("id") or self.MISSING_DATA)
                    else:
                        owners.append(hb or self.MISSING_DATA)
                entity_name = ", ".join(owners)
            else:
                entity_name = self.MISSING_DATA
                
            affected.append({
                "name": (r or {}).get("name", rid or self.MISSING_DATA),
                "entity": entity_name,
                "definition": (r or {}).get("description", (r or {}).get("comment", self.MISSING_DATA)),
                "unit": (r or {}).get("unit", self.MISSING_DATA)
            })

        # Resolve dependsOnParameters
        depends = []
        for ref in process.get("dependsOnParameters", []):
            pid = self._resolve_ref(ref)
            p = parameters_by_id.get(pid) if pid else None
            depends.append({
                "name": (p or {}).get("name", pid or self.MISSING_DATA),
                "entity": "Parameter",
                "definition": (p or {}).get("description", (p or {}).get("comment", self.MISSING_DATA)),
                "unit": (p or {}).get("unit", self.MISSING_DATA)
            })

        return {
            "name": process.get("name", "Sans nom"),
            "description": process.get("description", self.DEFAULT_DESC),
            "input_attrs": involved,
            "output_attrs": affected,
            "depended_parameters": depends,
            "equation": process.get("equation"),
            "pseudoCode": process.get("pseudoCode")
        }

    # ---------- Entity rendering (reuse of structure and tables) ----------
    def _build_entity(self, entity: Dict) -> str:
        """Construit la documentation pour un agent (entité) + ressources + dynamiques."""
        sections = [
            f"## Entité : {entity.get('name', 'Sans nom')} ({entity.get('id', self.MISSING_DATA)})",
            self._build_description(entity),
            self._build_attributes_section(entity),  # ressources remappées
            self._build_operations_section(entity),  # processus (dynamiques)
        ]
        return "\n\n".join(filter(None, sections))

    def _build_description(self, entity: Dict) -> str:
        """Section description."""
        try:
            description = (entity.get('description') or entity.get('comment') or "").strip()
            content = ["### Documentation"]
            content.append(description if description else self.DEFAULT_DESC)
            return "\n".join(content)
        except Exception as e:
            logger.warning(f"Erreur description entité: {str(e)}")
            return "### Documentation\n" + self.EMPTY_SECTION

    def _build_attributes_section(self, entity: Dict) -> str:
        """Section attributs (affiche les ressources de l'agent en tableau)."""
        attrs = entity.get('attributes', [])
        content = ["### Attributs"]
        content.append("\nLes ressources détenues par l'agent :\n")
        content.append(self._build_attributes_table(attrs))
        return "\n".join(content)

    def _build_attributes_table(self, attributes: List[Dict]) -> str:
        headers = ["Paramètre", "Commentaire", "Unité"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        rows = []
        for attr in attributes:
            rows.append(
                f"| `{attr.get('name', '?')}` | "
                f"{attr.get('description', self.MISSING_DATA)} | "
                f"{attr.get('type', self.MISSING_DATA)} |"
            )
        if not rows:
            rows.append(f"| {' | '.join(['...'] * len(headers))} |")
        return "\n".join([header_row, separator] + rows)

    def _build_operations_section(self, entity: Dict) -> Optional[str]:
        """Section dynamiques: liste des processus où l'agent est sujet."""
        try:
            processes = entity.get('processes', [])
            content = ["### Dynamiques"]
            if processes:
                for process in processes:
                    process_content = self._build_single_process(process)
                    if process_content:
                        content.append(process_content)
            else:
                content.append(self.EMPTY_SECTION)
            return "\n\n".join(content)
        except Exception as e:
            logger.warning(f"Erreur section Dynamiques: {str(e)}")
            return "### Dynamiques\n" + self.EMPTY_SECTION

    def _build_single_process(self, process: Dict) -> Optional[str]:
        """Processus: documentation + tableaux (inputs, outputs, params) + équation + pseudo-code."""
        try:
            if not isinstance(process, dict) or not process.get('name'):
                return None

            sections = [
                f"#### Processus: {process['name']}",
                f"##### Documentation :\n {process.get('description', self.DEFAULT_DESC)}",
                self._build_attributes_usage(process),
                self._build_behavior_subsection(process),
                self._build_pseudocode_snippet(process)
            ]
            return "\n".join(filter(None, sections))
        except Exception as e:
            logger.warning(f"Erreur processus {process.get('name')}: {str(e)}")
            return None

    def _build_attributes_usage(self, process: Dict) -> str:
        """Variables d'entrée/sortie + paramètres."""
        input_vars = process.get('input_attrs', [])
        output_vars = process.get('output_attrs', [])
        depended_params = process.get('depended_parameters', [])
        content = ["\n##### Attributs"]

        content.append("\nLe processus dépend des variables suivantes :\n")
        content.append(self._build_process_variables_table(
            input_vars,
            headers=["Variables d'état", "Entité", "Définition", "Unité"]
        ))

        content.append("\nLe processus agit sur les variables suivantes :\n")
        content.append(self._build_process_variables_table(
            output_vars,
            headers=["Variables d'état", "Entité", "Définition", "Unité"]
        ))

        content.append("\net dépend des paramètres suivants :\n")
        content.append(self._build_process_variables_table(
            depended_params,
            headers=["Paramètres", "Entité", "Définition", "Unité"]
        ))
        return "\n".join(content)

    def _build_process_variables_table(self, variables: List[Dict], headers: List[str]) -> str:
        if not headers or len(headers) != 4:
            headers = ["Variables d'état", "Entité", "Définition", "Unité"]
        header_row = f"| {' | '.join(f'**{h}**' for h in headers)} |"
        separator = f"| {' | '.join(['---'] * len(headers))} |"
        rows = []
        for var in variables:
            rows.append(
                f"| {var.get('name', '...')} | "
                f"{var.get('entity', '...')} | "
                f"{var.get('definition', var.get('description', '...'))} | "
                f"{var.get('unit', var.get('type', '...'))} |"
            )
        if not rows:
            rows.append(f"| {' | '.join(['...'] * len(headers))} |")
        return "\n".join([header_row, separator] + rows)

    def _build_behavior_subsection(self, process: Dict) -> str:
        """Équation et note comportement."""
        try:
            content = ["\n##### Comportement"]
            content.append("\n*Description détaillée du processus (équations, états, activités, etc.).*\n")
            equation = process.get('equation')
            if equation and str(equation).strip():
                eq_str = str(equation).strip()
                parts = [p.strip() for p in eq_str.split(';') if p.strip()]
                if len(parts) == 1:
                    content.append(f"\n###### Équation : \n`{parts[0]}`")
                else:
                    content.append("\n###### Équation :")
                    for p in parts:
                        content.append(f"\n`{p}`")
            else:
                content.append(f"\n###### Équation : {self.MISSING_DATA_MESSAGE} \n")
            return ''.join(content)
        except Exception:
            return "##### Comportement \n" + self.MISSING_DATA_MESSAGE

    def _build_pseudocode_snippet(self, process: Dict) -> Optional[str]:
        pseudo = process.get('pseudoCode', '')
        content = ["##### Pseudo-code"]
        content.append("\n*Pseudo-code tel que fourni par le modèle.*\n")
        if pseudo and str(pseudo).strip():
            # Restaurer les retours à la ligne
            formatted = pseudo.replace("\\n", "\n")
            # Ne pas strip, juste rstrip pour éviter un \n final
            formatted = textwrap.dedent(formatted).rstrip()
            content.append("```python\n" + formatted + "\n```")
        else:
            content.append(self.MISSING_DATA_MESSAGE + "\n")
        return "\n".join(content)

