# yaml_to_json.py (version étendue)
import yaml
import json
from typing import Dict, Any

yaml_file_path = 'input.yml'
json_file_path = 'output.json'

def yaml_to_json(yaml_file_path: str, json_file_path: str):
    try:
      """Conversion YAML vers JSON avec validation de schéma basique"""
      with open(yaml_file_path, mode='r', encoding='utf-8') as yaml_file:
          yaml_object = yaml.safe_load(yaml_file)
      
      # Validation basique de la structure d'initialisation
      '''
      if 'initialization' in yaml_object:
          validated_data = _validate_initialization_schema(yaml_object)
      else:
          validated_data = yaml_object
      '''
      
      with open(json_file_path, mode='w', encoding='utf-8') as json_file:
          # json.dump(validated_data, json_file, indent=4, ensure_ascii=False)
          json.dump(yaml_object, json_file, indent=4, ensure_ascii=False)
      
      print(f"YAML data successfully converted to JSON")

    except Exception as e:
      print(f"Erreur de conversion : {str(e)}")

'''
def _validate_initialization_schema(data: Dict) -> Dict:
  """Validation basique du schéma d'initialisation"""
  required_sections = ['metadata', 'entities', 'parameters', 'state_variables']
      
  for section in required_sections:
    if section not in data:
      print(f"Warning: Missing section '{section}' in initialization data")    
      
  return data  
'''  



# Nouvelle fonction pour le répertoire multi-fichiers YAML
def yaml_directory_to_json(yaml_directory: str, json_file_path: str):
    """Combine plusieurs fichiers YAML en un seul JSON"""
    from pathlib import Path
    import glob
    
    combined_data = {}
    yaml_files = glob.glob(str(Path(yaml_directory) / "*.yaml")) + \
                 glob.glob(str(Path(yaml_directory) / "*.yml"))
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                file_data = yaml.safe_load(f)
                file_name = Path(yaml_file).stem
                combined_data[file_name] = file_data
        except Exception as e:
            print(f"Error loading {yaml_file}: {str(e)}")
    
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(combined_data, json_file, indent=4, ensure_ascii=False)


### Example of use
yaml_to_json(yaml_file_path, json_file_path)