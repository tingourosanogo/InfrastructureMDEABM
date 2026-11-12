import sys
import logging
import traceback
from typing import Optional, List
from pathlib import Path

# Configuration du chemin du projet
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
sys.path.insert(0, str(project_root))

# Imports des composants du pipeline
from src.gaml_generator.pseudocodeToaction.pseudocode_cleaner import PseudoCodeCleaner
from src.gaml_generator.pseudocodeToaction.lark_parser import LarkPseudoCodeParser
from src.gaml_generator.pseudocodeToaction.variable_tracker import VariableTracker
from src.gaml_generator.pseudocodeToaction.gaml_ast_transformer import GamlASTTransformer
from src.gaml_generator.pseudocodeToaction.gaml_emitter import GamlEmitter
from src.gaml_generator.process_gaml_generator import ProcessToGAMLConverter

# Simulation de ProcessModel (adapte à ta structure réelle si besoin)
class ProcessModel:
    def __init__(self, name: str, pseudoCode: str,
                 equation: Optional[str] = None,
                 description: Optional[str] = None,
                 dependsOnParameters: Optional[List[str]] = None):
        self.name = name
        self.pseudoCode = pseudoCode
        self.equation = equation
        self.description = description
        self.dependsOnParameters = dependsOnParameters or []

def test_process_to_gaml_converter():
    logger = logging.getLogger("test_process_to_gaml_converter")
    logger.setLevel(logging.DEBUG)

    # Chemins (adapte selon ta structure)
    grammar_path = project_root / "src" / "gaml_generator" / "pseudocodeToaction" / "pseudocode.lark"
    if not grammar_path.exists():
        logger.error(f"Fichier de grammaire introuvable : {grammar_path}")
        return

    # Instanciation du converter complet
    converter = ProcessToGAMLConverter(logger=logger, debug=True, generate_reflex_default=True)

    # ────────────────────────────────────────────────
    # Cas de test (pseudoCodes réalistes)
    # ────────────────────────────────────────────────
    test_cases = {
        "mineralization_simple": {
            "name": "Mineralization Process",
            "pseudoCode": """
soil_moisture = soil_moisture /* resource_053 */;
field_capacity_tmp = field_capacity /* resource_005 */;
moisture_factor = (soil_moisture / field_capacity_tmp);
if (moisture_factor > 1) {
  moisture_factor = 1;
}
soil_nitrogen /* resource_001 */ += moisture_factor * 0.5;
""",
            "equation": "N_min = moisture_factor * k_base",
            "description": "Processus de minéralisation simple",
            "depends_on": ["moisture_factor", "k_base"]
        },
        "conflict_resolution": {
            "name": "Conflict Resolution",
            "pseudoCode": """
if (conflict_detected) {
  ProbInformal = traditional_knowledge /* resource_044 */ * informal_mediation_factor /* property_134 */;
  if (random < ProbInformal) {
    conflict_resolved = true;
  } else {
    ProbFormal = governance_efficiency /* property_133 */;
    if (random < ProbFormal) {
      conflict_resolved = true;
    } else {
      conflict_resolved = false;
    }
  }
  if (conflict_resolved) {
    conflict_penalty_water += 0.0 /* property_164 */;
    conflict_penalty_seasonal_fodder -= 0.0 /* property_165 */;
  } else {
    conflict_penalty_water = 0.5;
    conflict_penalty_seasonal_fodder = 0.5;
  }
}
""",
            "equation": None,
            "description": "Résolution de conflit sur ressources",
            "depends_on": ["traditional_knowledge", "governance_efficiency"]
        },
        "empty_or_invalid": {
            "name": "Empty Process",
            "pseudoCode": "",
            "equation": None,
            "description": "Processus vide pour test",
            "depends_on": []
        }
    }

    print("\n" + "="*100)
    print("TEST UNITAIRE BOUT-EN-BOUT - ProcessToGAMLConverter")
    print("="*100 + "\n")

    all_success = True

    for name, params in test_cases.items():
        print(f"\n{'-'*100}")
        print(f"TEST : {name}")
        print(f"Nom processus : {params['name']}")
        print(f"Code brut d'entrée :\n{params['pseudoCode'].strip()}\n")

        try:
            model = ProcessModel(
                name=params['name'],
                pseudoCode=params['pseudoCode'],
                equation=params.get('equation'),
                description=params.get('description'),
                dependsOnParameters=params.get('depends_on')
            )

            gaml_code = converter.generate_gaml_code(model)

            print("GAML FINAL GÉNÉRÉ :")
            print("-" * 60)
            print(gaml_code)
            print("-" * 60)

            # Vérifications basiques
            checks = [
                f"action {params['name'].lower().replace(' ', '_')}" in gaml_code,
                "}" in gaml_code,
                params.get('description') is None or params['description'] in gaml_code,
                params.get('equation') is None or params['equation'] in gaml_code,
                "reflex" in gaml_code  # par défaut activé
            ]

            if all(checks):
                print("  → Vérifications OK ✓")
            else:
                print("  → Vérifications échouées ✗")
                all_success = False

        except Exception as e:
            print("  → ÉCHEC")
            print(traceback.format_exc())
            all_success = False

    print("\n" + "="*100)
    print("RÉSULTAT GLOBAL - ProcessToGAMLConverter")
    print("="*100)
    if all_success:
        print("TOUS LES TESTS ONT RÉUSSI ✓")
    else:
        print("CERTAINS TESTS ONT ÉCHOUÉ ✗")
    print("="*100 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_process_to_gaml_converter()