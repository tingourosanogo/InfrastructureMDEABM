# src/parsers/xmi_parser.py
import html
import re
import sys
import textwrap
from lxml import etree
from typing import Dict, List, Optional
from pathlib import Path
import logging

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

class ParserError(Exception):
    pass

NSMAP = {
    'xmi': "http://www.omg.org/XMI",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
    'ses': "http://www.example.org/socioecosystem.en"
}

class XMIParser:
    def __init__(self, xmi_path: str):
        self.xmi_path = xmi_path
        self.raw_content = None
        self.tree = self._load_xmi()

    def _load_xmi(self) -> etree._ElementTree:
        if not Path(self.xmi_path).exists():
            logger.error(f"Fichier XMI manquant: {self.xmi_path}")
            raise ParserError(f"Fichier manquant: {self.xmi_path}")
        
        with open(self.xmi_path, 'r', encoding='utf-8') as f:
            self.raw_content = f.read()

        parser = etree.XMLParser(remove_blank_text=False, recover=True, encoding='utf-8', huge_tree=True, resolve_entities=False, no_network=True, strip_cdata=True, remove_comments=False, remove_pis=False)
        try:
            tree = etree.parse(self.xmi_path, parser)
            logger.info(f"XMI chargé avec succès: {self.xmi_path}")
            return tree
        except etree.XMLSyntaxError as e:
            logger.error(f"Erreur syntaxe XMI {self.xmi_path}: {e}")
            raise ParserError(f"Erreur syntaxe XMI: {e}") from e

    def _extract_common_attributes(self, element: etree._Element) -> Dict:
        data = {
            'id': element.get('id') or element.get('{http://www.omg.org/XMI}id'),
            'name': element.get('name', ''),
            'description': element.get('description', ''),
            'comment': element.get('comment', ''),
            'type': element.get('type', ''),
            'unit': element.get('unit', ''),
            'value': element.get('value'), 
        }
        try:
            data['pos_x'] = float(element.get('pos_x', 0.0))
            data['pos_y'] = float(element.get('pos_y', 0.0))
        except ValueError:
            logger.warning("Valeurs pos_x/pos_y invalides, fallback à 0.0")
            data['pos_x'] = 0.0
            data['pos_y'] = 0.0
        return data

    def _extract_references(self, element: etree._Element, ref_name: str) -> List[str]:
        refs = []
        xpath_query = f'./ses:{ref_name}'
        for ref_element in element.xpath(xpath_query, namespaces=NSMAP):
            href = ref_element.get('href')
            if href and href.startswith('#'):
                refs.append(href[1:])
        return refs

    def _get_properties(self, ses_element: etree._Element) -> List[Dict]:
        properties_data = []
        # Utilisation de ./ses:properties pour cibler les propriétés de haut niveau du modèle
        for prop_element in ses_element.xpath('./ses:properties', namespaces=NSMAP):
            data = self._extract_common_attributes(prop_element)
            
            # Détermination du type XMI (Resource ou Parameter)
            xsi_type = prop_element.attrib.get(f"{{{NSMAP['xsi']}}}type")
            
            # Initialisation des attributs de valeur
            data['unit'] = self.normalize_unit(prop_element.attrib.get('unit', 'unitless'))
            initial_value = None

            if 'Resource' in xsi_type:
                data['emf_type'] = xsi_type.split(':')[-1]
                # La valeur initiale d'une Ressource est souvent dans l'attribut 'quantity'
                initial_value = prop_element.attrib.get('quantity')
                
            elif 'Parameter' in xsi_type:
                data['emf_type'] = xsi_type.split(':')[-1]
                # La valeur initiale d'un Paramètre est souvent dans l'attribut 'value'
                if prop_element.attrib.get('value'):
                    initial_value = prop_element.attrib.get('value')
                else:
                    initial_value = 0.0
            
            data['value'] = initial_value
            
            # Récupérer la définition
            data['definition'] = prop_element.attrib.get('description') or prop_element.attrib.get('comment', '')

            data['heldBy_refs'] = self._extract_references(prop_element, 'heldBy')
            properties_data.append(data)
        return properties_data

    # normalize unit    
    def normalize_unit(self, unit: str) -> str:
        if not unit:
            return "unitless"
        unit = unit.strip().lower()
        # Exemples de normalisation
        if "kg or liters" in unit:
            return "kg_or_liters"
        if "(" in unit or ")" in unit:
            return unit.replace("(", "").replace(")", "").replace(",", "_")
        return unit


    def _get_agents(self, ses_element: etree._Element) -> List[Dict]:
        agents_data = []
        for agent_element in ses_element.xpath('.//ses:agents', namespaces=NSMAP):
            data = self._extract_common_attributes(agent_element)
            # === LOGIQUE DE NOMBRE INITIAL (Initial Count) ===
            initial_count = agent_element.attrib.get('initial_count')
            if initial_count is not None:
                try:
                    # Conversion en int, car GAMA attend un nombre
                    data['initial_count'] = int(initial_count) 
                except ValueError:
                    data['initial_count'] = 0 
            else:
                # Laisser None: l'Assembler cherchera dans le JSON d'initialisation
                data['initial_count'] = None

            data['partOfParentAgent_ref'] = next(iter(self._extract_references(agent_element, 'partOfParentAgent')), None)
            agents_data.append(data)
        return agents_data

    # ====== Extraction des processus avec pseudoCode et equation ======
    def _get_processes(self, ses_element: etree._Element) -> List[Dict]:
        processes_data = []
        for proc_element in ses_element.xpath('.//ses:processes', namespaces=NSMAP):
            data = self._extract_common_attributes(proc_element)

            # EXTRACTION ROBUSTE DU PSEUDOCODE
            raw_pseudo = self.extract_pseudocode_perfectly(data['id'])
            data['pseudoCode'] = raw_pseudo
            data['equation'] = proc_element.attrib.get('equation')
            data['source'] = proc_element.attrib.get('source')
            data['destination'] = proc_element.attrib.get('destination')

            data['subjects_refs'] = self._extract_references(proc_element, 'subjects')
            data['involvedResources_refs'] = self._extract_references(proc_element, 'involvedResources')
            data['affectsResources_refs'] = self._extract_references(proc_element, 'affectsResources')

            processes_data.append(data)
        return processes_data

    def extract_pseudocode_perfectly(self, process_id: str) -> str:
        """
        Extrait le contenu de l'attribut pseudoCode sans la normalisation XML.
        """
        
        content = self.raw_content

        # 1. Regex ciblée : 
        # - On cherche le process avec l'ID spécifique
        # - On capture tout ce qui est dans pseudoCode="..." 
        # - Le flag re.DOTALL permet de capturer les vrais sauts de ligne (\n)
        pattern = rf'id="{process_id}".*?pseudoCode="([^"]+)"'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return ""

        # 2. Récupération de la capture (group 1)
        raw_pseudo = match.group(1)

        # 3. Décodage des entités HTML/XML (ex: &lt; devient <)
        # html.unescape est parfait ici car il ne touche pas aux espaces/sauts de ligne
        final_code = html.unescape(raw_pseudo)

        return final_code.strip()



    # ==== Méthode principale pour parser le modèle XMI et extraire les données structurées ====
    def parse_model(self) -> Dict:
        if not self.tree:
            raise ParserError("Arbre XMI non chargé.")
        root_element = self.tree.getroot()
        ses_element = root_element.xpath('./ses:SocioEcosystem', namespaces=NSMAP)
        if not ses_element:
            logger.error("Élément SocioEcosystem manquant dans XMI.")
            raise ParserError("Élément SocioEcosystem manquant.")
        ses_element = ses_element[0]
        model_data = {
            'properties': self._get_properties(ses_element),
            'agents': self._get_agents(ses_element),
            'processes': self._get_processes(ses_element),
        }
        # Validation basique
        if not any(model_data.values()):
            logger.warning("Modèle XMI vide (aucune entité extraite).")
        logger.info("XMI parsé avec succès.")
        return model_data
    
