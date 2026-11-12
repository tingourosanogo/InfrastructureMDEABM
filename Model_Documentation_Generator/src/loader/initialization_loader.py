# initialization_loader.py
import json
from pathlib import Path
from typing import Dict, Any
import sys
import shutil

# Configure le path Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
from src.parsers.yaml_to_json import yaml_to_json
from src.parsers.parser_csv_to_json_initialization import csv_to_json

class InitializationLoader:
    def __init__(self):
        self.supported_formats = ['multi-csv', 'yaml', 'json']
    
    def load_initialization_data(self, input_path: str, output_path: str, input_format: str = None, delimitor: str = None):
        """Charge les données d'initialisation depuis différents formats"""
        path = Path(input_path)
        
        # Détection automatique du format
        if input_format is None or (input_format!="yaml" and input_format!="json" and input_format!="csv" and input_format!="multi-csv"):
            if path.is_dir() or path.suffix == '.csv':
                input_format = 'multi-csv'  # Par défaut pour les répertoires CSV
            elif path.suffix in ['.yaml', '.yml']:
                input_format = 'yaml'
            elif path.suffix == '.json':
                input_format = 'json'
        
         # Option 1: Chargement depuis CSV
        if input_format == 'multi-csv' and path.is_dir():
            csv_to_json(input_path, output_path, delimitor)
                  
         # Option 2: Chargement depuis YAML
        elif input_format == 'yaml':
            yaml_to_json(input_path, output_path)
        
        # Option 3: Chargement depuis JSON
        elif input_format == 'json':
            shutil.copy(input_path, output_path)
            with open(output_path, 'r', encoding='utf-8') as f:
                return json.load(f)
            
        
        else:
            raise ValueError(f"Initialisation - Unsupported format: {input_format}")
    
    def validate_initialization_data(self, data: Dict) -> bool:
        """Validation basique des données d'initialisation"""
        required_keys = ['entities', 'parameters']
        return all(key in data for key in required_keys)