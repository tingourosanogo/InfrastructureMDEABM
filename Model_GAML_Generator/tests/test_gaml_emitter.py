import sys
import logging
import traceback
from pathlib import Path

# Configuration du chemin du projet
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
sys.path.insert(0, str(project_root))

# Imports
from src.gaml_generator.pseudocodeToaction.gaml_emitter import GamlEmitter, EmissionConfig, EmissionResult


def test_gaml_emitter_full_pipeline():
    """
    Test unitaire complet du GamlEmitter avec exécution de tout le pipeline
    (Cleaner → Parser → Collector → Transformer → Emitter)
    """
    logger = logging.getLogger("test_gaml_emitter")
    logger.setLevel(logging.DEBUG)

    # Configuration de l'emitter
    config = EmissionConfig(
        indent_size=4,
        generate_reflex=True,
        reflex_suffix="_dynamics",
        include_header_comments=True,
        minify=False
    )

    emitter = GamlEmitter(logger=logger, config=config)

    # ────────────────────────────────────────────────
    # Cas de test réalistes
    # ────────────────────────────────────────────────
    test_cases = {
        "cas complet avec annotations et opérateurs": {
            "process_name": "Mineralization Process",
            "pseudo_code": """
        procedure update_soil_data(float threshold, int soil_layers) {
            for each layer in soil_layers {
                if (layer_moisture < threshold) {
                    irrigate(layer);
                }
            }
        }

        function calculate_yield(float base_value) {
            if (is_drought) {
                return base_value * 0.5;
            }
            return base_value;
        }


""",
            "equation": "k = k_base * temp_factor * moisture_factor * ph_factor * cn_factor",
            "description": "Processus de minéralisation de la matière organique",
            "depends_on": ["temp_factor", "moisture_factor", "ph_factor"]
        }
    }

    print("\n" + "="*110)
    print("TESTS UNITAIRES - GamlEmitter (Pipeline Complet)")
    print("="*110 + "\n")

    all_success = True

    for name, params in test_cases.items():
        print(f"\n{'─'*100}")
        print(f"TEST : {name}")
        print(f"Processus : {params['process_name']}\n")

        try:
            # Appel de la méthode haut-niveau qui exécute tout le pipeline
            result: EmissionResult = emitter.generate_from_pseudo_code(
                process_name=params['process_name'],
                pseudo_code=params['pseudo_code'],
                equation=params.get('equation'),
                description=params.get('description'),
                depends_on=params.get('depends_on')
            )

            print("Code GAML généré :")
            print("-" * 90)
            print(result.code)
            print("-" * 90)

            # Vérifications automatiques
            normalized = result.process_name
            checks = [
                f"action {normalized} {{" in result.code,
                "}" in result.code,
                len(result.code) > 100,                     # code non trivial
                "do " + normalized in result.code,          # reflex présent
            ]

            if all(checks):
                print(" → Vérifications structurelles OK ✓")
            else:
                print(" → Certaines vérifications ont échoué ✗")
                all_success = False

            if result.warnings:
                print(f" ⚠️  Warnings ({len(result.warnings)}):")
                for w in result.warnings:
                    print(f"    - {w}")

        except Exception as e:
            print(" → ÉCHEC")
            print(traceback.format_exc())
            all_success = False

    print("\n" + "="*110)
    print("RÉSULTAT GLOBAL - GamlEmitter Full Pipeline")
    print("="*110)
    if all_success:
        print("TOUS LES TESTS ONT RÉUSSI ✓")
    else:
        print("CERTAINS TESTS ONT ÉCHOUÉ ✗")
    print("="*110 + "\n")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s:%(name)s: %(message)s'
    )
    test_gaml_emitter_full_pipeline()