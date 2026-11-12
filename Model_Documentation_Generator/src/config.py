from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class DocConfig:
    title: str = "Documentation du Modèle"
    authors: List[Dict[str, str]] = None
    version: str = "1.0.0"
    
    class StructureConfig:
        show_derived: bool = True
        group_by_type: bool = True
        skip_empty: bool = True

    