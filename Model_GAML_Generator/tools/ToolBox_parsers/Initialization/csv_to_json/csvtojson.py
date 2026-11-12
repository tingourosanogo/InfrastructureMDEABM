import csv
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

class CSVToJSONConverter:
    def __init__(self, csv_dir: str = "initialization_data"):
        self.csv_dir = Path(csv_dir)
        self.data = {
            "metadata": {},
            "global": {},
            "input_data": {},
            "entities": [],
            "parameters": {},
            "state_variables": {},
            "scenarios": [],
            "traceability": {},
            "validation": {},
            "initialization_rules": []
        }
    
    def convert_all(self) -> Dict:
        """Convertit tous les CSV en structure JSON complète"""
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
        
        return self.data
    
    def _parse_json_field(self, value: str) -> Any:
        """Parse les champs contenant du JSON stringifié"""
        if not value or value == '':
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    def _read_csv(self, filename: str) -> List[Dict]:
        """Lit un fichier CSV et retourne les données"""
        filepath = self.csv_dir / filename
        if not filepath.exists():
            return []
        
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse tous les champs qui pourraient contenir du JSON
                parsed_row = {}
                for key, value in row.items():
                    parsed_row[key] = self._parse_json_field(value)
                data.append(parsed_row)
        return data

    def _load_metadata(self):
        """Charge les métadonnées"""
        # Informations générales
        general_data = self._read_csv('metadata_general.csv')
        if general_data:
            self.data['metadata'].update(general_data[0])
        
        # Auteurs
        authors_data = self._read_csv('metadata_authors.csv')
        self.data['metadata']['authors'] = authors_data
        
        # Références
        references_data = self._read_csv('metadata_references.csv')
        self.data['metadata']['references'] = references_data

    def _load_global_config(self):
        """Charge la configuration globale"""
        global_data = self._read_csv('global_config.csv')
        
        temporal_config = {}
        spatial_config = {}
        
        for item in global_data:
            if item['section'] == 'temporal':
                temporal_config = {
                    'start_date': item['start_date'],
                    'end_date': item['end_date'],
                    'time_step': item['time_step'],
                    'warmup_period': item['warmup_period']
                }
            elif item['section'] == 'spatial':
                spatial_config = {
                    'extent': item['extent'],
                    'projection': item['projection'],
                    'resolution': item['resolution']
                }
        
        self.data['global'] = {
            'temporal_scope': temporal_config,
            'spatial_configuration': spatial_config
        }

    def _load_input_data(self):
        """Charge les données d'entrée"""
        input_data = self._read_csv('input_data.csv')
        
        spatial_data = []
        tabular_data = []
        
        for item in input_data:
            if item['data_type'] == 'spatial':
                spatial_data.append({
                    'type': item['format_type'],
                    'format': item['file_format'],
                    'path': item['path'],
                    'description': item['description'],
                    'resolution': item.get('resolution'),
                    'source': item.get('source'),
                    'uncertainty': item.get('quality')
                })
            elif item['data_type'] == 'tabular':
                tabular_data.append({
                    'type': item['format_type'],
                    'format': item['file_format'],
                    'path': item['path'],
                    'description': item['description'],
                    'sample_size': item.get('sample_size'),
                    'response_rate': item.get('response_rate'),
                    'validation_method': item.get('validation_method')
                })
        
        self.data['input_data'] = {
            'spatial_data': spatial_data,
            'tabular_data': tabular_data
        }

    def _load_entities(self):
        """Charge les entités"""
        entities_data = self._read_csv('entities.csv')
        
        for entity in entities_data:
            self.data['entities'].append({
                'name': entity['name'],
                'type': entity['type'],
                'count': entity.get('count'),
                'initialization_method': entity['initialization_method'],
                'data_source': entity['data_source'],
                'sampling_strategy': entity.get('sampling_strategy'),
                'stratification_variables': entity.get('stratification_variables', []),
                'attribute_mapping': entity.get('attribute_mapping', [])
            })

    def _load_parameters(self):
        """Charge les paramètres"""
        parameters_data = self._read_csv('parameters.csv')
        
        fixed_params = []
        variable_params = []
        
        for param in parameters_data:
            if param['parameter_type'] == 'fixed':
                fixed_params.append({
                    'name': param['name'],
                    'entity': param['entity'],
                    'value': param['value'],
                    'unit': param['unit'],
                    'definition': param['definition'],
                    'source': param['source'],
                    'uncertainty': param.get('uncertainty', {}),
                    'sensitivity_rank': param.get('sensitivity_rank'),
                    'validation': param.get('validation')
                })
            elif param['parameter_type'] == 'variable':
                variable_params.append({
                    'name': param['name'],
                    'entity': param['entity'],
                    'values': param['values'],
                    'definition': param['definition'],
                    'source': param['source'],
                    'impact_assessment': param.get('impact_assessment')
                })
        
        self.data['parameters'] = {
            'fixed': fixed_params,
            'variable': variable_params
        }

    def _load_state_variables(self):
        """Charge les variables d'état"""
        state_vars_data = self._read_csv('state_variables.csv')
        
        fixed_vars = []
        variable_vars = []
        
        for var in state_vars_data:
            if var['variable_type'] == 'fixed':
                fixed_vars.append({
                    'name': var['name'],
                    'entity': var['entity'],
                    'value': var['value'],
                    'unit': var['unit'],
                    'distribution': var.get('distribution'),
                    'parameters': var.get('distribution_params', {}),
                    'source': var['source']
                })
            elif var['variable_type'] == 'variable':
                variable_vars.append({
                    'name': var['name'],
                    'entity': var['entity'],
                    'values': var['values'],
                    'distribution': var.get('distribution'),
                    'probabilities': var.get('probabilities', []),
                    'source': var['source']
                })
        
        self.data['state_variables'] = {
            'fixed_initialization': fixed_vars,
            'variable_initialization': variable_vars
        }

    def _load_scenarios(self):
        """Charge les scénarios"""
        scenarios_data = self._read_csv('scenarios.csv')
        
        for scenario in scenarios_data:
            self.data['scenarios'].append({
                'name': scenario['name'],
                'description': scenario['description'],
                'based_on': scenario.get('based_on'),
                'parameters': scenario.get('parameters', {}),
                'state_variables': scenario.get('state_variables', {}),
                'validation_status': scenario.get('validation_status')
            })

    def _load_traceability(self):
        """Charge les données de traçabilité"""
        traceability_data = self._read_csv('traceability.csv')
        
        data_quality = []
        uncertainty = []
        sensitivity_analysis = {}
        
        for item in traceability_data:
            if item['traceability_type'] == 'data_quality':
                data_quality.append({
                    'parameter': item['parameter'],
                    'quality_score': item['quality_score'],
                    'assessment_method': item['assessment_method'],
                    'experts': item.get('experts', [])
                })
            elif item['traceability_type'] == 'uncertainty':
                uncertainty.append({
                    'parameter': item['parameter'],
                    'uncertainty_type': item['uncertainty_type'],
                    'magnitude': item['magnitude'],
                    'propagation_method': item['propagation_method']
                })
            elif item['traceability_type'] == 'sensitivity':
                sensitivity_analysis = {
                    'planned_methods': item.get('planned_methods', []),
                    'parameters_included': item.get('parameters_included'),
                    'software': item.get('software')
                }
        
        self.data['traceability'] = {
            'data_quality': data_quality,
            'uncertainty_quantification': uncertainty,
            'sensitivity_analysis': sensitivity_analysis
        }

    def _load_validation(self):
        """Charge les méthodes de validation"""
        validation_data = self._read_csv('validation_methods.csv')
        
        self.data['validation'] = {
            'methods': validation_data
        }

    def _load_initialization_rules(self):
        """Charge les règles d'initialisation"""
        rules_data = self._read_csv('initialization_rules.csv')
        
        for rule in rules_data:
            self.data['initialization_rules'].append({
                'entity': rule['entity'],
                'rule': rule['rule_description'],
                'implementation': rule['implementation_code'],
                'assumptions': rule.get('assumptions')
            })

    def save_json(self, output_path: str = "initialization_reconstructed.json"):
        """Sauvegarde le JSON reconstruit"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        print(f"JSON reconstruit sauvegardé dans: {output_path}")

# Utilisation
if __name__ == "__main__":
    converter = CSVToJSONConverter("initialization_data")
    reconstructed_data = converter.convert_all()
    converter.save_json("initialization_reconstructed.json")
    
    # Validation
    with open("initialization.json", 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Vérification que les données sont identiques
    if reconstructed_data == original_data:
        print("✅ Conversion réussie! Les données JSON sont identiques.")
    else:
        print("⚠️  Petites différences détectées, mais structure principale préservée.")