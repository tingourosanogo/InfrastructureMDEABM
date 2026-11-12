"""
Ressource XMI personnalisée pour la sérialisation SocioEcosystem.
Corrige les problèmes de sérialisation des références non-contenantes PyEcore.
Aligné sur le métamodèle actuel.
"""
from pyecore.resources.xmi import XMIResource, XMIOptions, XMI_URL, XSI_URL
from lxml.etree import QName, Element, ElementTree
from pyecore.ecore import EObject
import logging

# Configuration du logger
logger = logging.getLogger('socio_ecosystem.xml_resource')


class XMLResource(XMIResource):
    """
    Ressource XMI personnalisée pour le modèle SocioEcosystem.
    
    Responsabilités :
    - Correction de la sérialisation des références non-contenantes
    - Gestion des namespaces spécifiques au métamodèle
    - Transformation des attributs en éléments href
    """
    
    # Namespace du métamodèle SocioEcosystem ACTUEL
    SOCIO_NAMESPACE = 'http://www.example.org/socioecosystem.en'
    
    
    # Références non-contenantes du MÉTAMODÈLE ACTUEL
    REFERENCES_TO_FIX = [
        # Relations Agent
        'holdsResources',     # Agent → Resource
        'containsAgents',     # Agent → Agent (containment)
        'isSubjectOf',        # Agent → Process (inverse)
        'isObjectOf',         # Agent → Process (inverse)
        
        # Relations Process  
        'involvedResources',  # Process → Resource
        'dependsOnParameters', # Process → Parameter
        
        # Relations TransformationProcess
        'affectsResources',   # TransformationProcess → Resource
        
        # Relations MovementProcess
        'source',             # MovementProcess → Agent
        'destination'         # MovementProcess → Agent
    ]

    def __init__(self, uri=None, use_uuid=False):
        """
        Initialise la ressource XML personnalisée.
        
        Args:
            uri: URI de la ressource
            use_uuid (bool): Utiliser les UUID pour les IDs
        """
        super().__init__(uri, use_uuid)

        #self.uri_fragment_map = {}
        #if not hasattr(self, 'uri_fragment_map'):
        #    self.uri_fragment_map = {}
        #if not hasattr(self, '_later'):
        #    self._later = []
        self._later = []
        self.prefixes = {}
        self.reverse_nsmap = {}
        self.parse_information = []

    def get_parse_information(self):
        """
        Retourne les informations de parsing pour le débogage.
        
        Returns:
            list: Informations de parsing collectées
        """
        return self.parse_information

    def save(self, output=None, options=None):
        """
        Surcharge la méthode save pour appliquer la sérialisation href personnalisée.
        
        Args:
            output: Flux de sortie
            options: Options de sérialisation
            
        Returns:
            URI fermée
        """
        self.options = options or {}
        output = self.open_out_stream(output)
        self.prefixes.clear()
        self.reverse_nsmap.clear()
        
        serialize_default = self.options.get(XMIOptions.SERIALIZE_DEFAULT_VALUES, False)

        # Configuration des namespaces pour le métamodèle
        nsmap = self._configure_namespaces()
        
        # Génération de l'arbre XML initial avec PyEcore
        xmi_root = self._generate_initial_xml(serialize_default, nsmap)
        
        # Application des corrections de sérialisation
        self._apply_custom_serialization(xmi_root)
        
        # Écriture du fichier final
        self._write_final_xml(xmi_root, output)
        
        return self.uri.close_stream()

    def _configure_namespaces(self):
        """
        Configure les namespaces pour la sérialisation.
        
        Returns:
            dict: Mapping des namespaces
        """
        return {
            None: self.SOCIO_NAMESPACE,  # Namespace par défaut
            'xsi': XSI_URL,
            'xmi': XMI_URL,
            'ses': self.SOCIO_NAMESPACE  # Préfixe explicite
        }

    def _generate_initial_xml(self, serialize_default, nsmap):
        """
        Génère l'arbre XML initial avec la sérialisation PyEcore standard.
        
        Args:
            serialize_default (bool): Inclure les valeurs par défaut
            nsmap (dict): Mapping des namespaces
            
        Returns:
            Element: Racine XMI générée
        """
        if len(self.contents) == 1:
            root = self.contents[0]
            self.register_eobject_epackage(root)
            tmp_xmi_root = self._go_across(root, serialize_default)
        else:
            # Cas multiple racines (non standard)
            tag = QName(self.SOCIO_NAMESPACE, 'SocioEcosystem')
            tmp_xmi_root = Element(tag)
            for root in self.contents:
                root_node = self._go_across(root, serialize_default)
                tmp_xmi_root.append(root_node)

        # Fusion des namespaces
        nsmap.update(self.prefixes)
        xmi_root = Element(tmp_xmi_root.tag, nsmap=nsmap)
        xmi_root[:] = tmp_xmi_root[:]
        xmi_root.attrib.update(tmp_xmi_root.attrib)
        
        return xmi_root

    def _apply_custom_serialization(self, xmi_root):
        """
        Applique les corrections de sérialisation personnalisées.
        
        Args:
            xmi_root: Racine de l'arbre XML à corriger
        """
        # Correction des références non-contenantes
        self._fix_non_containing_references(xmi_root)

    def _fix_non_containing_references(self, xmi_root):
        """
        Corrige la sérialisation des références non-contenantes.
        
        Transforme les attributs en éléments avec href selon le métamodèle actuel.
        
        Args:
            xmi_root: Racine de l'arbre XML
        """
        for element in xmi_root.iter():
            if self._is_socio_element(element):
                self._process_element_references(element)

    def _is_socio_element(self, element):
        """
        Vérifie si un élément appartient au namespace SocioEcosystem.
        
        Args:
            element: Élément XML à vérifier
            
        Returns:
            bool: True si c'est un élément SocioEcosystem
        """
        return element.tag.startswith(f'{{{self.SOCIO_NAMESPACE}}}')

    def _process_element_references(self, element):
        """
        Traite les références d'un élément spécifique selon le métamodèle actuel.
        
        Args:
            element: Élément XML à traiter
        """
        for ref_name in self.REFERENCES_TO_FIX:
            attrib_value = element.get(ref_name)
            
            if attrib_value:
                # Supprimer l'attribut incorrect
                element.attrib.pop(ref_name)
                
                # Créer des éléments href pour chaque référence
                self._create_href_elements(element, ref_name, attrib_value)

    def _create_href_elements(self, parent, ref_name, attrib_value):
        """
        Crée des éléments href pour une référence.
        
        Args:
            parent: Élément parent XML
            ref_name (str): Nom de la référence
            attrib_value (str): Valeur de l'attribut (IDs séparés par des espaces)
        """
        ids = attrib_value.split()
        
        for item_id in ids:
            if item_id.strip():  # Ignorer les IDs vides
                href_element = Element(ref_name, href=f"#{item_id.strip()}")
                parent.append(href_element)

    def _write_final_xml(self, xmi_root, output):
        """
        Écrit l'arbre XML final dans le flux de sortie.
        
        Args:
            xmi_root: Racine de l'arbre XML final
            output: Flux de sortie
        """
        try:
            tree = ElementTree(xmi_root)
            tree.write(output,
                      pretty_print=True,
                      xml_declaration=True,
                      encoding='UTF-8')
            output.flush()
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture XML : {e}")
            raise
    
    def _decode_attribute(self, owner, key, value, element=None):
        """
        Surcharge pour garantir que l'attribut 'id' (modèle) ou 'xmi:id' 
        est enregistré dans la carte de résolution avant toute résolution de proxy.
        """
        namespace, att_name = self.extract_namespace(key)
        
        # Vérifie si l'attribut est 'id' (modèle) ou 'xmi:id' (résolution)
        is_xmi_id = namespace == self.XMI_NAMESPACE and att_name == 'id'
        is_model_id = not namespace and att_name == 'id'
        
        # 1. Enregistrement forcé de l'ID (LE CŒUR DE LA SOLUTION)
        if is_xmi_id or is_model_id:
            # La valeur (ex: 'agent_002') est la clé, l'objet Ecore (owner) est la valeur
            self.uri_fragment_map[value] = owner
        
        # 2. Déléguer le reste de la logique au chargeur XMI standard
        # Le parent va gérer les xsi:type, les href et l'attribution de la valeur
        # pour l'attribut 'id' du modèle (le feature).
        return super()._decode_attribute(owner, key, value, element=element)
    