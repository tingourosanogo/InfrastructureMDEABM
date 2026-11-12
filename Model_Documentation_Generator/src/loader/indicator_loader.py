# indicator_loader.py
import json
from pathlib import Path
from typing import Dict
import sys
import shutil

# Configure le path Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
from src.parsers.yaml_to_json import yaml_to_json
from src.parsers.parser_csv_to_json_indicator import csv_to_json

class IndicatorLoader:
    def __init__(self):
        self.supported_formats = ['csv', 'yaml', 'json']
    
    def load_indicator_data(self, input_path: str, output_path: str, input_format: str = None, delimitor: str = None):
        """Charge les données d'indicateurs depuis différents formats"""
        path = Path(input_path)
        
        # Détection automatique du format
        if input_format is None or (input_format!="yaml" and input_format!="json" and input_format!="csv"):
            if path.suffix == '.csv':
                input_format = 'csv'  # Par défaut pour les répertoires CSV
            elif path.suffix in ['.yaml', '.yml']:
                input_format = 'yaml'
            elif path.suffix == '.json':
                input_format = 'json'
        
        
        if input_format == 'csv':
            csv_to_json(input_path, output_path, delimitor)
        
        elif input_format == 'yaml':
            yaml_to_json(input_path, output_path)
        
        elif input_format == 'json':
            shutil.copy(input_path, output_path)
            with open(output_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        else:
            raise ValueError(f"Indicator - Unsupported format: {input_format}")
    
  