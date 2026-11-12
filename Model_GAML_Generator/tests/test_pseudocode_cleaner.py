# tests/test_pseudocode_cleaner.py
import sys
import logging
from pathlib import Path

# Configuration du chemin du projet
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
sys.path.insert(0, str(project_root))

from src.gaml_generator.pseudocodeToaction.pseudocode_cleaner import PseudoCodeCleaner

def test_cleaner_on_mineralization():
    logger = logging.getLogger("test_cleaner")
    cleaner = PseudoCodeCleaner(logger=logger)

    pseudocode = """
      // Get raw milk input
      raw_milk_input = milk_for_processing /* resource_029 */;
      processing_efficiency = dairy_processing_efficiency /* property_117 */;

      if raw_milk_input &gt; 0:
        // Calculate final product output
        product_output = raw_milk_input * processing_efficiency;

        // 1. Consume raw milk input
        milk_for_processing = milk_for_processing - raw_milk_input; /* resource_029 */

        // 2. Increase final product stock
        Dairy_Product_Stock = Dairy_Product_Stock + product_output; /* resource_026 */
      else:
        product_output = 0;
    """

    result = cleaner.clean(pseudocode)

    print("\n=== Code nettoyé ===")
    for line in result.code.splitlines():
        print(line)

    print("\n=== Warnings ===")
    for w in result.warnings:
        print(w)

    print("\n=== Annotations détectées ===")
    for a in result.annotations:
        print(a)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_cleaner_on_mineralization()
