import sys
import logging
import traceback
from pathlib import Path

# Configuration du chemin du projet
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
sys.path.insert(0, str(project_root))


# Imports des composants du pipeline
from src.gaml_generator.pseudocodeToaction.pseudocode_cleaner import PseudoCodeCleaner
from src.gaml_generator.pseudocodeToaction.lark_parser import LarkPseudoCodeParser
from src.gaml_generator.pseudocodeToaction.variable_collector import VariableCollector, print_variable_summary

def test_variable_collector_pipeline():
    logger = logging.getLogger("test_variable_collector_pipeline")
    logger.setLevel(logging.DEBUG)

    grammar_path = project_root / "src" / "gaml_generator" / "pseudocodeToaction" / "pseudocode.lark"
    if not grammar_path.exists():
        logger.error(f"Fichier de grammaire introuvable : {grammar_path}")
        return

    # Instanciation des composants
    cleaner = PseudoCodeCleaner(logger=logger)
    parser = LarkPseudoCodeParser(grammar=grammar_path, logger=logger, debug=True, strict=False)
    collector = VariableCollector(logger=logger)

    test_cases = {
        "fertilization": """
        soil_nitrogen = soil_nitrogen /* resource_001 */;
        fertilizer_stock_current = fertilizer_stock /* resource_015 */;
        soil_moisture = soil_moisture /* resource_053 */;
        soil_pH = soil_pH /* resource_052 */;
        max_nitrogen = max_nitrogen /* property_087 */;
        """
    }

    print("\n" + "="*100)
    print("TESTS UNITAIRES - PIPELINE : Cleaner → Lark Parser → VariableCollector")
    print("="*100 + "\n")

    all_success = True

    for name, raw_code in test_cases.items():
        print(f"\n{'-'*80}")
        print(f"TEST : {name}")
        print(f"Code brut d'entrée :\n{raw_code.strip()}\n")

        try:
            # Étape 1 : Nettoyage
            cleaned = cleaner.clean(raw_code.strip())
            print("  Étape 1 - Nettoyage OK")
            print(f"  Code nettoyé :\n{cleaned.code}\n")

            # Étape 2 : Parsing Lark
            parse_result = parser.parse(cleaned)
            if parse_result.is_valid():
                print("  Étape 2 - Parsing Lark OK")
                print(parse_result.pretty_print())
            else:
                print("  → Parsing échoué")
                print(parse_result.pretty_print())
                all_success = False
                continue

            # Étape 3 : Collecte des variables
            collection_result = collector.collect_from_parse_result(parse_result)
            print("  Étape 3 - Collecte des variables OK")
            print_variable_summary(collection_result)

            print("  Test réussi ✓")

        except Exception as e:
            print("  → ÉCHEC")
            print(traceback.format_exc())
            all_success = False

    print("\n" + "="*100)
    print("RÉSULTAT GLOBAL DU PIPELINE")
    print("="*100)
    if all_success:
        print("TOUS LES TESTS ONT RÉUSSI ✓")
    else:
        print("CERTAINS TESTS ONT ÉCHOUÉ ✗")
    print("="*100 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_variable_collector_pipeline()
