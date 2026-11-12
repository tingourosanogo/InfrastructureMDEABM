#!/usr/bin/env python3
# user_manual_loader.py
import logging
import json
import sys
from typing import Dict, Any
from pathlib import Path
import sys
import shutil

# Configure le path Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
from src.parsers.yaml_to_json import yaml_to_json

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserManual_Loader:
    def __init__(self):
        self.supported_formats = ['csv', 'yaml', 'json']
    
    def load_userManual_data(self, input_path: str, output_path: str, input_format: str = None):
        """Charge les données de Mode d'utilisateur depuis différents formats"""
        path = Path(input_path)
        
        
        # Détection automatique du format
        if input_format is None or (input_format!="yaml" and input_format!="json"):
            if path.suffix in ['.yaml', '.yml']:
                input_format = 'yaml'
            elif path.suffix == '.json':
                input_format = 'json'
     
        
        # Option 1: Chargement depuis YAML
        if input_format == "yaml":
            yaml_to_json(input_path, output_path)
                        
        # Option 2: Chargement depuis JSON
        elif input_format == 'json':
            shutil.copy(input_path, output_path)
            with open(output_path, 'r', encoding='utf-8') as f:
                return json.load(f)
            
        else:
            raise ValueError(f"Mode d'emploi - Unsupported format: {input_format}")
        
        


    
