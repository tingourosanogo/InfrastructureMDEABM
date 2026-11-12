# Converting CSV to JSON in Python can be achieved using either the built-in json and csv modules or the pandas library.
import csv
import json
import sys
def flatten_item(item):
    """Transforme les listes imbriquées en chaînes formatées"""
    flattened = item.copy()
    
    # Gestion des variables
    if 'variables' in flattened:
        flattened['variables'] = '|'.join(
            f"{v['name']}:{v.get('entity', '')}:{v.get('definition', '')}:{v.get('unit', '')}"
            for v in item['variables']
        )
    
    # Gestion des paramètres
    if 'parameters' in flattened:
        flattened['parameters'] = '|'.join(
            f"{p['name']}:{p.get('entity', '')}:{p.get('definition', '')}:{p.get('unit', '')}"
            for p in item['parameters']
        )
    
    return flattened

# Define file paths
if len(sys.argv) == 3:
    # execute with arguments
    print("Usage: python script.py <input_json_file> <output_csv_file>")
    json_file_path = sys.argv[1]
    csv_file_path = sys.argv[2]
elif len(sys.argv) == 1:
    # execute without arguments
    csv_file_path = 'indicators.csv'
    json_file_path = 'indicators.json'
else:
    sys.exit(1)



def parse_nested(text: str) -> list:
    """Parse les champs imbriqués style 'name:unit' ou 'name:value:unit'"""
    return [item.split(':') for item in text.split('|')] if text else []

"""
Using csv and json modules (Standard Approach):
Import necessary modules.
    import csv
    import json
"""

def json_to_csv():
    """Convertit le JSON en CSV avec encodage UTF-8"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        
        # Extraction des indicateurs
        indicators = data.get('indicators', [])

        # separator
        csv_delimiter = ';'

        # Determine fieldnames (headers)
        if data:
            fieldnames = indicators[0].keys()
        else:
            fieldnames = [] # Handle empty JSON data
        
        if not indicators:
            print("Aucune donnée d'indicateur trouvée")
            return
        
        # Open CSV file in write mode with specified delimiter
        with open(csv_file_path, 'w', encoding='utf-8-sig', newline='') as csvfile:  # utf-8-sig pour Excel
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=csv_delimiter)
            writer.writeheader()
            
            for item in indicators:
                writer.writerow(flatten_item(item))
        
        print(f"Conversion réussie : {csv_file_path} with semicolon ({csv_delimiter}) separator ")
    
    except Exception as e:
        print(f"Erreur de conversion : {str(e)}")

if __name__ == "__main__":
    json_to_csv()
