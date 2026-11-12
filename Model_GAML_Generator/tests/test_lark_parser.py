# tests/test_lark_parser.py
import sys
import logging
from pathlib import Path

# Configuration du chemin du projet
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
sys.path.insert(0, str(project_root))

# Imports des composants du pipeline
from src.gaml_generator.pseudocodeToaction.pseudocode_cleaner import PseudoCodeCleaner
from src.gaml_generator.pseudocodeToaction.lark_parser import LarkPseudoCodeParser

def test_lark_parser():
    logger = logging.getLogger("test_lark_parser")
    logger.setLevel(logging.DEBUG)

    grammar_path = project_root / "src" / "gaml_generator" / "pseudocodeToaction" / "pseudocode.lark"
    if not grammar_path.exists():
        logger.error(f"Fichier de grammaire introuvable : {grammar_path}")
        return

    cleaner = PseudoCodeCleaner(logger=logger)
    parser = LarkPseudoCodeParser(grammar=grammar_path, logger=logger, debug=True, strict=False)

    valid_cases = {
        "fertilization": """
        for depth = 1 to 5 step 2 {
            if (depth > 2) {
                moisture_factor = 0.5;
                apply_subsoil_logic();
            }
        }
        """
    }

    print("\n" + "="*80)
    print("TESTS LARK PARSER - CAS VALIDES")
    print("="*80 + "\n")

    all_success = True
    for name, raw_code in valid_cases.items():
        print(f"\n--- Test valide : {name} ---")
        try:
            # Étape 1 : Nettoyage
            cleaned = cleaner.clean(raw_code.strip())
            print("  Étape 1 - Nettoyage OK")
            print(f"  Code nettoyé :\n{cleaned.code}\n")

            # Étape 2 : Parsing Lark
            result = parser.parse(cleaned)
            if result.is_valid():
                print("  Étape 2 - Parsing Lark OK")
                print(result.pretty_print())
                print("  AST simplifié :")
                print(result.tree.pretty(indent_str="    "))
                print("  Succès ✓")
            else:
                print("  → Parsing échoué")
                print(result.pretty_print())
                all_success = False
        except Exception as e:
            print("  → ÉCHEC inattendu")
            logger.exception(e)
            all_success = False

    print("\n" + "="*80)
    print("RÉSULTAT GLOBAL")
    print("="*80)
    if all_success:
        print("TOUS LES TESTS ONT RÉUSSI ✓")
    else:
        print("CERTAINS TESTS ONT ÉCHOUÉ ✗")
    print("="*80 + "\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_lark_parser()
