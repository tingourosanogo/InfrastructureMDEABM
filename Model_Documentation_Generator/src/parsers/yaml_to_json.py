import yaml
import json


"""
Install yaml (if not already installed).
  pip install PyYAML
or
  pip install ruamel.yaml
"""


def yaml_to_json(yaml_file_path: str, json_file_path: str):
    # Read Yaml data 
    with open(yaml_file_path, mode='r', encoding='utf-8') as yaml_file:
        yaml_object = yaml.safe_load(yaml_file)
        # yaml_object = yaml.load(yaml_file)  # directly load without safe when we use ruamel.yaml


    # Write the data to a JSON file
    with open(json_file_path, mode='w', encoding='utf-8') as json_file:
        json.dump(yaml_object, json_file, indent=4, ensure_ascii=False)



# Nouvelle fonction pour le repertoire multi-fichiers YAML
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
