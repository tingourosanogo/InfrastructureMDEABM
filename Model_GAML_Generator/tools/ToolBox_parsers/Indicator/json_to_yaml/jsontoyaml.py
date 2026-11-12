import yaml
import json


"""
Install yaml (if not already installed).
  pip install PyYAML
or
  pip install ruamel.yaml
"""

json_file_path = 'indicators.json'
yaml_file_path = 'indicators.yml'


def json_to_yaml():
    try:
      # Read Json data 
      with open(json_file_path, mode='r', encoding='utf-8') as json_file:
          json_data = json.load(json_file)


      # Write the data to a JSON file
      with open(yaml_file_path, mode='w', encoding='utf-8') as yaml_file:
              yaml.dump(
                  json_data,
                  yaml_file,
                  allow_unicode=True,  # Préserve les caractères spéciaux
                  sort_keys=False,     # Garde l'ordre original
                  indent=5,           # Indentation lisible
                  width=80,           # Largeur de ligne
                  default_flow_style=False  # Style bloc
              )
      
      print(f"JSON data successfully converted to YAML")

    except Exception as e:
        print(f"Erreur de conversion : {str(e)}")


### Example of use
json_to_yaml()
