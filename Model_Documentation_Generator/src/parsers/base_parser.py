from abc import ABC, abstractmethod
from lxml import etree

class BaseParser(ABC):
    def __init__(self, xmi_path: str):
        self.tree = etree.parse(xmi_path)
        self.ns = {
            'xmi': 'http://schema.omg.org/spec/XMI/2.1',
            'uml': 'http://www.eclipse.org/uml2/3.0.0/UML'
        }

    @abstractmethod
    def parse(self):
        pass