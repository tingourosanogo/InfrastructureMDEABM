import json
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

class JSONToCSVConverter:
    def __init__(self, json_path: str, output_dir: str = "initialization_data"):
        self.json_path = json_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.data = self._load_json()
    
    def _load_json(self) -> Dict:
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def convert_all(self):
        """Convertit toutes les sections en CSV"""
        self.convert_metadata()
        self.convert_global_config()
        self.convert_input_data()
        self.convert_entities()
        self.convert_parameters()
        self.convert_state_variables()
        self.convert_scenarios()
        self.convert_traceability()
        self.convert_validation()
        self.convert_initialization_rules()
    
    def _write_csv(self, filename: str, data: List[Dict], fieldnames: List[str]):
        """Écrit un fichier CSV avec gestion des valeurs complexes"""
        with open(self.output_dir / filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                processed_row = {}
                for key, value in row.items():
                    if isinstance(value, (list, dict)):
                        processed_row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        processed_row[key] = value
                writer.writerow(processed_row)

    def convert_metadata(self):
        """Convertit les métadonnées"""
        metadata = self.data['metadata']
        
        # Auteurs
        authors_data = []
        for author in metadata['authors']:
            authors_data.append({
                'model_name': metadata['model_name'],
                'author_name': author['name'],
                'affiliation': author['affiliation'],
                'role': author['role'],
                'orcid': author.get('orcid', '')
            })
        self._write_csv('metadata_authors.csv', authors_data, 
                       ['model_name', 'author_name', 'affiliation', 'role', 'orcid'])
        
        # Références
        references_data = []
        for ref in metadata['references']:
            references_data.append({
                'model_name': metadata['model_name'],
                'citation': ref['citation'],
                'doi': ref.get('doi', '')
            })
        self._write_csv('metadata_references.csv', references_data,
                       ['model_name', 'citation', 'doi'])
        
        # Informations générales
        general_data = [{
            'model_name': metadata['model_name'],
            'protocol': metadata['protocol'],
            'version': metadata['version'],
            'creation_date': metadata['creation_date'],
            'last_modified': metadata['last_modified']
        }]
        self._write_csv('metadata_general.csv', general_data,
                       ['model_name', 'protocol', 'version', 'creation_date', 'last_modified'])

    def convert_global_config(self):
        """Convertit la configuration globale"""
        global_data = self.data['global']
        
        config_data = [{
            'section': 'temporal',
            'start_date': global_data['temporal_scope']['start_date'],
            'end_date': global_data['temporal_scope']['end_date'],
            'time_step': global_data['temporal_scope']['time_step'],
            'warmup_period': global_data['temporal_scope']['warmup_period']
        }, {
            'section': 'spatial',
            'extent': json.dumps(global_data['spatial_configuration']['extent']),
            'projection': global_data['spatial_configuration']['projection'],
            'resolution': global_data['spatial_configuration']['resolution']
        }]
        
        self._write_csv('global_config.csv', config_data,
                       ['section', 'start_date', 'end_date', 'time_step', 'warmup_period', 
                        'extent', 'projection', 'resolution'])

    def convert_input_data(self):
        """Convertit les données d'entrée"""
        input_data = self.data['input_data']
        
        # Données spatiales
        spatial_data = []
        for item in input_data['spatial_data']:
            spatial_data.append({
                'data_type': 'spatial',
                'format_type': item['type'],
                'file_format': item['format'],
                'path': item['path'],
                'description': item['description'],
                'resolution': item.get('resolution', ''),
                'source': item.get('source', ''),
                'quality': item.get('uncertainty', item.get('reliability', ''))
            })
        
        # Données tabulaires
        tabular_data = []
        for item in input_data['tabular_data']:
            tabular_data.append({
                'data_type': 'tabular',
                'format_type': item['type'],
                'file_format': 'csv',
                'path': item['path'],
                'description': item['description'],
                'sample_size': item.get('sample_size', ''),
                'response_rate': item.get('response_rate', ''),
                'validation_method': item.get('validation_method', '')
            })
        
        all_data = spatial_data + tabular_data
        self._write_csv('input_data.csv', all_data,
                       ['data_type', 'format_type', 'file_format', 'path', 'description',
                        'resolution', 'source', 'quality', 'sample_size', 'response_rate', 
                        'validation_method'])

    def convert_entities(self):
        """Convertit les entités"""
        entities_data = []
        for entity in self.data['entities']:
            entities_data.append({
                'name': entity['name'],
                'type': entity['type'],
                'count': entity.get('count', ''),
                'initialization_method': entity['initialization_method'],
                'data_source': entity['data_source'],
                'sampling_strategy': entity.get('sampling_strategy', ''),
                'stratification_variables': json.dumps(entity.get('stratification_variables', [])),
                'attribute_mapping': json.dumps(entity.get('attribute_mapping', []))
            })
        
        self._write_csv('entities.csv', entities_data,
                       ['name', 'type', 'count', 'initialization_method', 'data_source',
                        'sampling_strategy', 'stratification_variables', 'attribute_mapping'])

    def convert_parameters(self):
        """Convertit les paramètres"""
        parameters = self.data['parameters']
        
        # Paramètres fixes
        fixed_params = []
        for param in parameters['fixed']:
            fixed_params.append({
                'parameter_type': 'fixed',
                'name': param['name'],
                'entity': param['entity'],
                'value': param['value'],
                'unit': param['unit'],
                'definition': param['definition'],
                'source': param['source'],
                'uncertainty': json.dumps(param.get('uncertainty', {})),
                'sensitivity_rank': param.get('sensitivity_rank', ''),
                'validation': param.get('validation', '')
            })
        
        # Paramètres variables
        variable_params = []
        for param in parameters['variable']:
            variable_params.append({
                'parameter_type': 'variable',
                'name': param['name'],
                'entity': param['entity'],
                'values': json.dumps(param['values']),
                'definition': param['definition'],
                'source': param['source'],
                'impact_assessment': param.get('impact_assessment', '')
            })
        
        all_params = fixed_params + variable_params
        self._write_csv('parameters.csv', all_params,
                       ['parameter_type', 'name', 'entity', 'value', 'values', 'unit',
                        'definition', 'source', 'uncertainty', 'sensitivity_rank',
                        'validation', 'impact_assessment'])

    def convert_state_variables(self):
        """Convertit les variables d'état"""
        state_vars = self.data['state_variables']
        
        # Variables fixes
        fixed_vars = []
        for var in state_vars['fixed_initialization']:
            fixed_vars.append({
                'variable_type': 'fixed',
                'name': var['name'],
                'entity': var['entity'],
                'value': var['value'],
                'unit': var['unit'],
                'distribution': var.get('distribution', ''),
                'distribution_params': json.dumps(var.get('parameters', {})),
                'source': var['source']
            })
        
        # Variables variables
        variable_vars = []
        for var in state_vars['variable_initialization']:
            variable_vars.append({
                'variable_type': 'variable',
                'name': var['name'],
                'entity': var['entity'],
                'values': json.dumps(var['values']),
                'distribution': var.get('distribution', ''),
                'probabilities': json.dumps(var.get('probabilities', [])),
                'source': var['source']
            })
        
        all_vars = fixed_vars + variable_vars
        self._write_csv('state_variables.csv', all_vars,
                       ['variable_type', 'name', 'entity', 'value', 'values', 'unit',
                        'distribution', 'distribution_params', 'probabilities', 'source'])

    def convert_scenarios(self):
        """Convertit les scénarios"""
        scenarios_data = []
        for scenario in self.data['scenarios']:
            scenarios_data.append({
                'name': scenario['name'],
                'description': scenario['description'],
                'based_on': scenario.get('based_on', ''),
                'parameters': json.dumps(scenario.get('parameters', {})),
                'state_variables': json.dumps(scenario.get('state_variables', {})),
                'validation_status': scenario.get('validation_status', '')
            })
        
        self._write_csv('scenarios.csv', scenarios_data,
                       ['name', 'description', 'based_on', 'parameters', 
                        'state_variables', 'validation_status'])

    def convert_traceability(self):
        """Convertit la traçabilité"""
        traceability = self.data.get('traceability', {})
        
        # Qualité des données
        data_quality = []
        for item in traceability.get('data_quality', []):
            data_quality.append({
                'traceability_type': 'data_quality',
                'parameter': item['parameter'],
                'quality_score': item['quality_score'],
                'assessment_method': item['assessment_method'],
                'experts': json.dumps(item.get('experts', []))
            })
        
        # Incertitude
        uncertainty = []
        for item in traceability.get('uncertainty_quantification', []):
            uncertainty.append({
                'traceability_type': 'uncertainty',
                'parameter': item['parameter'],
                'uncertainty_type': item['uncertainty_type'],
                'magnitude': item['magnitude'],
                'propagation_method': item['propagation_method']
            })
        
        # Analyse de sensibilité
        sensitivity = []
        if traceability.get('sensitivity_analysis'):
            sens = traceability['sensitivity_analysis']
            sensitivity.append({
                'traceability_type': 'sensitivity',
                'planned_methods': json.dumps(sens.get('planned_methods', [])),
                'parameters_included': sens.get('parameters_included', ''),
                'software': sens.get('software', '')
            })
        
        all_traceability = data_quality + uncertainty + sensitivity
        if all_traceability:
            self._write_csv('traceability.csv', all_traceability,
                           ['traceability_type', 'parameter', 'quality_score', 
                            'assessment_method', 'experts', 'uncertainty_type',
                            'magnitude', 'propagation_method', 'planned_methods',
                            'parameters_included', 'software'])

    def convert_validation(self):
        """Convertit les méthodes de validation"""
        validation_data = []
        for method in self.data['validation']['methods']:
            validation_data.append({
                'method_name': method['name'],
                'validation_date': method.get('date', ''),
                'participants': method.get('participants', ''),
                'period': method.get('period', ''),
                'metric': method.get('metric', ''),
                'metric_value': method.get('value', ''),
                'threshold': method.get('threshold', ''),
                'result': method.get('result', '')
            })
        
        self._write_csv('validation_methods.csv', validation_data,
                       ['method_name', 'validation_date', 'participants', 'period',
                        'metric', 'metric_value', 'threshold', 'result'])

    def convert_initialization_rules(self):
        """Convertit les règles d'initialisation"""
        rules_data = []
        for rule in self.data['initialization_rules']:
            rules_data.append({
                'entity': rule['entity'],
                'rule_description': rule['rule'],
                'implementation_code': rule['implementation'],
                'assumptions': rule.get('assumptions', '')
            })
        
        self._write_csv('initialization_rules.csv', rules_data,
                       ['entity', 'rule_description', 'implementation_code', 'assumptions'])

# Utilisation
if __name__ == "__main__":
    converter = JSONToCSVConverter("initialization.json")
    converter.convert_all()
    print("Conversion terminée! Fichiers CSV générés dans le dossier 'initialization_data'")