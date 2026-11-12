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
from src.gaml_generator.pseudocodeToaction.variable_collector import VariableCollector
from src.gaml_generator.pseudocodeToaction.gaml_ast_transformer import GamlASTTransformer

def test_gaml_ast_transformer_pipeline():
    logger = logging.getLogger("test_gaml_ast_transformer_pipeline")
    logger.setLevel(logging.DEBUG)

    grammar_path = project_root / "src" / "gaml_generator" / "pseudocodeToaction" / "pseudocode.lark"
    if not grammar_path.exists():
        logger.error(f"Fichier de grammaire introuvable : {grammar_path}")
        return

    # Instanciation des composants
    cleaner = PseudoCodeCleaner(logger=logger)
    parser = LarkPseudoCodeParser(grammar=grammar_path, logger=logger, debug=True)
    collector = VariableCollector(logger=logger)
    transformer = GamlASTTransformer(logger=logger)

    test_cases = {
        "mineralization": """
// Step 1: calculate Environmental Rate Factor (k) based on temp, moisture, pH, c/n ratio
      // Temperature effect  
      soil_temp = soil_temperature /* resource_063 */;
      temp_factor = exp(0.069 * (soil_temp - 10)); 
      if (temp_factor &lt; 0) {
        temp_factor = 0;
      }

      // Moisture effect 
      soil_moisture = soil_moisture /* resource_053 */; 
      field_capacity_tmp = field_capacity /* resource_005 */;
      moisture_factor = (soil_moisture / field_capacity_tmp);
      if (moisture_factor &gt; 1) {
        moisture_factor = 1;
      }
      if (moisture_factor &lt; 0.2) {
        moisture_factor = 0;
      }

      // pH effect
      soil_pH_tmp = soil_pH /* resource_052 */;
      ph_factor = min(1, max(0, (soil_pH_tmp - 4)/(7 - 4))); 

      // c/n ratio effect
      cn_ratio_tmp = cn_ratio /* property_032 */;
      cn_factor = min(1, max(0, (25 - cn_ratio_tmp)/15)); 

      // calculate mineralization rate
      k_base = base_mineralization_rate_k_base /* property_033 */;
      k = k_base * temp_factor * moisture_factor * ph_factor * cn_factor;

      // Step 2: Determine actual mass to mineralize (Robustness check)
      rate = k * time_step; // k is the proportion of stock mineralized

      // consumable organic stocks (current values)
      litter_leaf_stock = leaf_litter /* resource_006 */;
      litter_natural_stock = litter_natural /* resource_007 */;
      litter_cultivated_stock = litter_cultivated /* resource_008 */;
      manure_stock = manure /* resource_031 */;

      // calculate consumed mass for each stock, capped at current stock availability
      consumed_leaf = min(litter_leaf_stock * rate, litter_leaf_stock);
      consumed_natural = min(litter_natural_stock * rate, litter_natural_stock);
      consumed_cultivated = min(litter_cultivated_stock * rate, litter_cultivated_stock);
      consumed_manure = min(manure_stock * rate, manure_stock);

      // Step 3: calculate Mineralized n and c
      n_from_leaf = consumed_leaf * leaf_litter_to_n /* property_046 */;
      n_from_natural = consumed_natural * natural_litter_to_n /* property_002 */;
      n_from_cultivated = consumed_cultivated * cultivated_litter_to_n /* property_083 */;
      n_from_manure = consumed_manure * manure_to_n /* property_085 */;
      n_mineralized = n_from_leaf + n_from_natural + n_from_cultivated + n_from_manure; // Total Mineralized nitrogen

      c_from_leaf = consumed_leaf * leaf_litter_to_c /* property_004 */;
      c_from_natural = consumed_natural * natural_litter_to_c /* property_001 */;
      c_from_cultivated = consumed_cultivated * cultivated_litter_to_c /* property_003 */;
      c_from_manure = consumed_manure * manure_to_c /* property_084 */;
      c_mineralized = c_from_leaf + c_from_natural + c_from_cultivated + c_from_manure; // Total Mineralized carbon 

      // Step 4: Update Resources (Mineral Pools increase, Organic Stocks decrease)
      soil_nitrogen /* resource_001 */ = soil_nitrogen + n_mineralized; 
      soil_carbon /* resource_002 */ = soil_carbon + c_mineralized; 

      leaf_litter /* resource_006 */ = leaf_litter - consumed_leaf; 
      natural_litter /* resource_007 */ = natural_litter - consumed_natural; 
      cultivated_litter /* resource_008 */ = cultivated_litter - consumed_cultivated;
      manure /* resource_031 */ = manure - consumed_manure;
"""
    }

    print("\n" + "="*100)
    print("TESTS UNITAIRES - PIPELINE COMPLET : Cleaner → Lark Parser → VariableCollector → GamlASTTransformer")
    print("="*100 + "\n")

    all_success = True

    for name, raw_code in test_cases.items():
        print(f"\n{'-'*100}")
        print(f"TEST : {name}")
        print(f"Code brut d'entrée :\n{raw_code.strip()}\n")

        try:
            # Étape 1 : Nettoyage
            cleaned = cleaner.clean(raw_code.strip())
            print("  Étape 1 - Nettoyage OK")
            print(f"  Code nettoyé :\n{cleaned.code}\n")

            # Étape 2 : Parsing Lark
            parse_result = parser.parse(cleaned)
            if parse_result.success:
                print("  Étape 2 - Parsing Lark OK")
                print(parse_result.tree.pretty(indent_str="    "))
            else:
                print("  → Parsing échoué")
                all_success = False
                continue

            # Étape 3 : Collecte des variables
            collection_result = collector.collect_from_parse_result(parse_result)
            print("  Étape 3 - Collecte des variables OK")
            print(collection_result.to_dict())

            # Étape 4 : Transformation en GAML
            translated_body = transformer.transform(parse_result, collection_result)
            print("  Étape 4 - Corps GAML traduit :")
            print(translated_body if translated_body.strip() else "    (Corps vide - vérifiez le transformer)")

            print("  Test réussi ✓")

        except Exception as e:
            print("  → ÉCHEC")
            print(traceback.format_exc())
            all_success = False

    print("\n" + "="*100)
    print("RÉSULTAT GLOBAL DU PIPELINE COMPLET")
    print("="*100)
    if all_success:
        print("TOUS LES TESTS ONT RÉUSSI ✓")
    else:
        print("CERTAINS TESTS ONT ÉCHOUÉ ✗")
    print("="*100 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_gaml_ast_transformer_pipeline()
