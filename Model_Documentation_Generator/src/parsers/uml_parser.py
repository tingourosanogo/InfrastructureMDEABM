from lxml import etree
from typing import Dict, List
from pathlib import Path
import sys

# Configure le path Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
from src.exceptions import InvalidModelError

class UMLParser:
    def __init__(self, xmi_path: str):
        try:
            self.tree = etree.parse(xmi_path)
            self.ns = {
                'xmi': "http://schema.omg.org/spec/XMI/2.1",
                'uml': "http://www.eclipse.org/uml2/3.0.0/UML"
            }
        except Exception as e:
            raise InvalidModelError(f"Erreur de parsing XMI: {str(e)}")

    def parse_to_structure(self) -> Dict:
        """Formatte les données pour StructureSection"""
        try:
            return {
                "entities": [
                    self._parse_class(cls) 
                    for cls in self.tree.xpath("//packagedElement[@xmi:type='uml:Class']", namespaces=self.ns)
                ]
            }
        except Exception as e:
            raise InvalidModelError(f"Erreur transformation structure: {str(e)}")

    def _parse_class(self, cls) -> Dict:
        return {
            "name": cls.get("name", "Sans nom"),
            "attributes": self._parse_attributes(cls),
            "processes": self._parse_operations(cls)
        }

    def _parse_attributes(self, cls) -> List[Dict]:
        return [{
            "name": attr.get("name"),
            "type": attr.get("type", "Non typé"),
            "is_derived": "derived" in attr.get("name", "").lower()
        } for attr in cls.xpath(".//ownedAttribute", namespaces=self.ns)]

    def _parse_operations(self, cls) -> List[Dict]:
        return [{
            "name": op.get("name"),
            "parameters": self._parse_parameters(op)
        } for op in cls.xpath(".//ownedOperation", namespaces=self.ns)]

    def _parse_parameters(self, op) -> List[str]:
        return [
            f"{param.get('name')}: {param.get('type', 'Any')}"
            for param in op.xpath(".//ownedParameter", namespaces=self.ns)
        ]