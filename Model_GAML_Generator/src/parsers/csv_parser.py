# src/parsers/csv_parser.py

import csv
import json
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ParserError(Exception):
    """Exception custom pour erreurs de parsing."""
    pass

def parse_nested(text: str, expected_parts: int) -> list:
    if not text or not text.strip():
        return []
    result = []
    items = text.split('|')
    for item in items:
        if not item.strip(): continue
        parts = item.split(':')
        while len(parts) < expected_parts:
            parts.append('')
        result.append(parts[:expected_parts])
    return result

def load_indicator_csv(csv_file_path: str, delimitor: str = ',') -> List[Dict]:
    """Charge et parse CSV indicators avec validation."""
    indicators_list = []
    try:
        with open(csv_file_path, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            csv_reader = list(csv.DictReader(csvfile, delimiter=delimitor))
            
            for row in csv_reader:
                parsed_row = {k: v for k, v in row.items()}
                if 'variables' in parsed_row:
                    parsed_vars = parse_nested(parsed_row.pop('variables'), 4)
                    parsed_row['variables'] = [{'name': v[0], 'entity': v[1], 'definition': v[2], 'unit': v[3]} for v in parsed_vars]
                if 'parameters' in parsed_row:
                    parsed_params = parse_nested(parsed_row.pop('parameters'), 5)
                    parsed_row['parameters'] = [{'name': p[0], 'entity': p[1], 'definition': p[2], 'unit': p[3], 'value': p[4]} for p in parsed_params]
                indicators_list.append(parsed_row)
        
        # Validation basique
        if not indicators_list:
            raise ParserError("Liste d'indicateurs vide après parsing.")
        required_per_item = ['id', 'name', 'formula']
        for ind in indicators_list:
            missing = [k for k in required_per_item if k not in ind]
            if missing:
                logger.warning(f"Indicateur incomplet (id={ind.get('id', 'inconnu')}) : clés manquantes {missing}")
        
        logger.info(f"CSV indicators parsé avec succès : {len(indicators_list)} items.")
        return indicators_list
    except Exception as e:
        logger.error(f"Erreur parsing CSV indicators {csv_file_path}: {e}")
        raise ParserError(f"Erreur parsing CSV: {e}") from e

class InitializationCSVParser:
    """Parse multi-CSV pour initialization avec logging."""
    def __init__(self, csv_dir: str = "initialization_data", separator: str = ","):
        self.csv_dir = Path(csv_dir)
        self.delimitor = separator
        self.data = {
            "metadata": {}, "global": {}, "input_data": {}, "entities": [],
            "parameters": {"definitions":[]}, "state_variables": {"definitions":[]}, 
            "scenarios": [], "traceability": {}, "validation": {},
            "initialization_rules": []
        }
    
    def _read_csv(self, filename: str) -> List[Dict]:
        file_path = self.csv_dir / filename
        if not file_path.exists():
            logger.warning(f"Fichier CSV manquant: {file_path}")
            return []
        try:
            with open(file_path, mode='r', newline='', encoding='utf-8-sig') as csvfile:
                data = list(csv.DictReader(csvfile, delimiter=self.delimitor))
                logger.info(f"CSV lu : {file_path} ({len(data)} lignes)")
                return data
        except Exception as e:
            logger.error(f"Erreur lecture CSV {filename}: {e}")
            return []

    def _parse_json_field(self, value: str) -> Any:
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.warning(f"Erreur parsing JSON field: {e}")
            return value
    
    # Les méthodes _load_* restent similaires, mais avec logs si data vide
    def _load_metadata(self):
        metadata = self._read_csv('metadata.csv')
        if metadata:
            self.data['metadata'] = metadata[0]
        else:
            logger.warning("Metadata CSV vide ou manquant.")

    def _load_input_data(self):
        input_data = self._read_csv('input_data.csv')
        if input_data:
            self.data['input_data'] = {item['key']: self._parse_json_field(item['value']) for item in input_data}
        else:
            logger.warning("Input data CSV vide ou manquant.")

    def _load_entities(self):
        entities = self._read_csv('entities.csv')
        if entities:
            self.data['entities'] = entities
        else:
            logger.warning("Entities CSV vide ou manquant.")

    def _load_parameters(self):
        parameters = self._read_csv('parameters.csv')
        if parameters:
            self.data['parameters']['definitions'] = parameters
        else:
            logger.warning("Parameters CSV vide ou manquant.")

    def _load_state_variables(self):
        state_vars = self._read_csv('state_variables.csv')
        if state_vars:
            self.data['state_variables']['definitions'] = state_vars
        else:
            logger.warning("State variables CSV vide ou manquant.")

    def _load_scenarios(self):
        scenarios = self._read_csv('scenarios.csv')
        if scenarios:
            self.data['scenarios'] = scenarios
        else:
            logger.warning("Scenarios CSV vide ou manquant.")

    def _load_traceability(self):
        traceability = self._read_csv('traceability.csv')
        if traceability:
            self.data['traceability'] = {item['key']: item['value'] for item in traceability}
        else:
            logger.warning("Traceability CSV vide ou manquant.")

    def _load_validation(self):
        validation = self._read_csv('validation.csv')
        if validation:
            self.data['validation'] = {item['key']: item['value'] for item in validation}
        else:
            logger.warning("Validation CSV vide ou manquant.")

    def _load_initialization_rules(self):
        rules = self._read_csv('initialization_rules.csv')
        if rules:
            self.data['initialization_rules'] = rules
        else:
            logger.warning("Initialization rules CSV vide ou manquant.")

    def _load_global_config(self):
        global_config = self._read_csv('global_config.csv')
        if global_config:
            self.data['global'] = global_config[0]
        else:
            logger.warning("Global config CSV vide ou manquant.")

            

    def convert_all(self) -> Dict:
        self._load_metadata()
        self._load_global_config()  
        self._load_input_data()
        self._load_entities()
        self._load_parameters()
        self._load_state_variables()
        self._load_scenarios()
        self._load_traceability()
        self._load_validation()
        self._load_initialization_rules()
        
        # Validation globale basique
        required_keys = ['metadata', 'global', 'entities']
        missing = [k for k in required_keys if not self.data.get(k)]
        if missing:
            logger.warning(f"Sections manquantes dans initialization: {missing}")
        
        logger.info("Initialization multi-CSV parsé avec succès.")
        return self.data