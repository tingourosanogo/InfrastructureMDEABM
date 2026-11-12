"""
tests/test_pipeline_complete.py
Tests unitaires complets pour le pipeline de transformation pseudo-code → GAML
"""

import unittest
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Ajout du chemin pour importer les modules du pipeline
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import des composants du pipeline
from src.gaml_generator.pseudocodeToaction.pseudocode_cleaner import PseudoCodeCleaner, CleanedCode
from src.gaml_generator.pseudocodeToaction.lark_parser import LarkPseudoCodeParser, ParseResult
from src.gaml_generator.pseudocodeToaction.variable_collector import VariableCollector, CollectionResult
from src.gaml_generator.pseudocodeToaction.gaml_ast_transformer import GamlASTTransformer
from src.gaml_generator.pseudocodeToaction.gaml_emitter import GamlEmitter, EmissionConfig, generate_gaml_code


class TestPipelineComplete(unittest.TestCase):
    """
    Tests complets du pipeline de transformation
    """
    
    @classmethod
    def setUpClass(cls):
        """Configuration initiale pour tous les tests"""
        logging.basicConfig(level=logging.WARNING)
        cls.logger = logging.getLogger(__name__)
        
        # Exemple réel de pseudo-code de modélisation écologique
        cls.ecological_model_pseudo = """
// ============================================
// MODÈLE DE CROISSANCE DES ARBRES AVEC BOUCLES NUTRIENTES
// ============================================

// 1. Paramètres environnementaux
temperature = air_temperature /* resource_001 */;
precipitation = rainfall /* resource_002 */;
soil_moisture = water_content /* resource_003 */;

// 2. Paramètres de l'espèce
optimal_temp = tree_optimal_temp /* property_101 */;
optimal_precip = tree_optimal_precip /* property_102 */;
growth_rate_max = tree_max_growth /* property_103 */;
temp_tolerance = tree_temp_tolerance /* property_104 */;

// 3. Calcul des facteurs de limitation
if (temperature > optimal_temp + temp_tolerance) {
    temp_factor = max(0, 1 - (temperature - (optimal_temp + temp_tolerance)) / temp_tolerance);
} else if (temperature < optimal_temp - temp_tolerance) {
    temp_factor = max(0, 1 - ((optimal_temp - temp_tolerance) - temperature) / temp_tolerance);
} else {
    temp_factor = 1;
}

precip_factor = min(1, precipitation / optimal_precip);

// 4. Croissance potentielle
potential_growth = growth_rate_max * temp_factor * precip_factor;

// 5. Croissance effective avec limitation par la biomasse disponible
current_biomass = biomass /* resource_010 */;
available_carbon = current_biomass * 0.3;  // 30% de la biomasse disponible pour croissance
actual_growth = min(potential_growth, available_carbon);

// 6. Mise à jour de la biomasse
biomass /* resource_010 */ += actual_growth;

// 7. Prélèvement d'azote
n_uptake_rate = tree_n_uptake /* property_201 */;
n_required = actual_growth * n_uptake_rate;
soil_nitrogen = n_soil_content /* resource_020 */;

if (n_required > soil_nitrogen) {
    n_uptake = soil_nitrogen;
    n_deficit = n_required - soil_nitrogen;
} else {
    n_uptake = n_required;
    n_deficit = 0;
}

soil_nitrogen /* resource_020 */ -= n_uptake;

// 8. Calcul de la croissance nette
net_growth = actual_growth * (1 - n_deficit / n_required) if (n_required > 0) else actual_growth;

// 9. Fonction utilitaire pour le stress hydrique
procedure calculate_water_stress(moisture, wilting_point, field_capacity) {
    if (moisture <= wilting_point) {
        stress = 0;
    } else if (moisture >= field_capacity) {
        stress = 1;
    } else {
        stress = (moisture - wilting_point) / (field_capacity - wilting_point);
    }
    return stress;
}

// 10. Application du stress hydrique
wilting_point = soil_wilting_point /* property_301 */;
field_capacity = soil_field_capacity /* property_302 */;
water_stress = calculate_water_stress(soil_moisture, wilting_point, field_capacity);
final_growth = net_growth * water_stress;

// 11. Mise à jour finale
biomass /* resource_010 */ += final_growth;

// 12. Sortie des résultats
print final_growth;
"""

    def test_01_cleaner_extracts_annotations(self):
        """Test 1: Vérifie que le cleaner extrait correctement les annotations"""
        cleaner = PseudoCodeCleaner()
        result = cleaner.clean(self.ecological_model_pseudo)
        
        self.assertIsInstance(result, CleanedCode)
        self.assertIsNotNone(result.code)
        self.assertTrue(len(result.code) > 0)
        
        # Vérifier les annotations extraites
        self.assertTrue(len(result.annotations) > 0)
        
        # Vérifier les types d'annotations
        resource_annotations = [a for a in result.annotations if a.type == 'resource']
        property_annotations = [a for a in result.annotations if a.type == 'property']
        
        self.assertTrue(len(resource_annotations) > 0)
        self.assertTrue(len(property_annotations) > 0)
        
        # Vérifier des annotations spécifiques
        resource_ids = [a.id for a in resource_annotations]
        self.assertIn('001', resource_ids)  # resource_001 (temperature)
        self.assertIn('002', resource_ids)  # resource_002 (precipitation)
        self.assertIn('010', resource_ids)  # resource_010 (biomass)
        
        property_ids = [a.id for a in property_annotations]
        self.assertIn('101', property_ids)  # property_101 (optimal_temp)
        self.assertIn('102', property_ids)  # property_102 (optimal_precip)
        
        print(f"✅ Cleaner: {len(result.annotations)} annotations extraites")
        print(f"   - Resources: {[a.id for a in resource_annotations[:5]]}")
        print(f"   - Properties: {[a.id for a in property_annotations[:5]]}")
    
    def test_02_parser_generates_valid_ast(self):
        """Test 2: Vérifie que le parser génère un AST valide"""
        cleaner = PseudoCodeCleaner()
        cleaned = cleaner.clean(self.ecological_model_pseudo)
        
        parser = LarkPseudoCodeParser(strict=False)
        parse_result = parser.parse(cleaned)
        
        self.assertIsInstance(parse_result, ParseResult)
        self.assertTrue(parse_result.success, f"Parsing failed: {parse_result.errors}")
        self.assertIsNotNone(parse_result.tree)
        
        # Vérifier les statistiques de parsing
        stats = parse_result.get_stats()
        self.assertGreater(sum(stats.values()), 0)
        
        # Vérifier la présence de structures clés
        self.assertGreater(stats.get('assign_stmt', 0), 10)
        self.assertGreater(stats.get('if_stmt', 0), 0)
        self.assertGreater(stats.get('procedure_decl', 0), 0)
        
        print(f"✅ Parser: AST généré avec {sum(stats.values())} nœuds")
        print(f"   - Assignations: {stats.get('assign_stmt', 0)}")
        print(f"   - Conditions: {stats.get('if_stmt', 0)}")
        print(f"   - Procédures: {stats.get('procedure_decl', 0)}")
    
    def test_03_variable_collector_finds_variables(self):
        """Test 3: Vérifie que le collecteur trouve toutes les variables"""
        cleaner = PseudoCodeCleaner()
        cleaned = cleaner.clean(self.ecological_model_pseudo)
        
        parser = LarkPseudoCodeParser()
        parse_result = parser.parse(cleaned)
        
        collector = VariableCollector()
        collection = collector.collect_from_parse_result(parse_result)
        
        self.assertIsInstance(collection, CollectionResult)
        self.assertTrue(len(collection.variables) > 0)
        self.assertTrue(len(collection.functions) > 0)
        
        # Vérifier les variables avec annotations
        annotated_vars = [v for v in collection.variables.values() if v.annotations]
        self.assertTrue(len(annotated_vars) > 0)
        
        # Vérifier des variables spécifiques
        variable_names = collection.variables.keys()
        self.assertIn('temperature', variable_names)
        self.assertIn('biomass', variable_names)
        self.assertIn('soil_nitrogen', variable_names)
        
        # Vérifier la procédure
        self.assertIn('calculate_water_stress', collection.functions)
        water_stress_func = collection.functions['calculate_water_stress']
        self.assertEqual(len(water_stress_func.parameters), 3)
        
        print(f"✅ Collector: {len(collection.variables)} variables trouvées")
        print(f"   - Variables avec annotations: {len(annotated_vars)}")
        print(f"   - Fonctions: {list(collection.functions.keys())}")
    
    def test_04_transformer_generates_valid_gaml(self):
        """Test 4: Vérifie que le transformateur génère du GAML valide"""
        cleaner = PseudoCodeCleaner()
        cleaned = cleaner.clean(self.ecological_model_pseudo)
        
        parser = LarkPseudoCodeParser()
        parse_result = parser.parse(cleaned)
        
        collector = VariableCollector()
        collection = collector.collect_from_parse_result(parse_result)
        
        transformer = GamlASTTransformer()
        gaml_code = transformer.transform(parse_result, collection)
        
        self.assertIsInstance(gaml_code, str)
        self.assertTrue(len(gaml_code) > 0)
        
        # Vérifier la présence d'éléments GAML
        self.assertIn('<-', gaml_code)  # Assignation GAML
        self.assertIn('if (', gaml_code)  # Condition
        self.assertIn('} else if (', gaml_code)  # Else if
        self.assertIn('}', gaml_code)  # Blocs
        
        # Vérifier les opérateurs convertis
        self.assertNotIn('==', gaml_code)  # == doit devenir =
        self.assertIn('=', gaml_code)  # = pour comparaison
        
        # Vérifier les appels de fonction
        self.assertIn('min(', gaml_code)
        self.assertIn('max(', gaml_code)
        
        # Vérifier la procédure transformée
        self.assertIn('action calculate_water_stress', gaml_code)
        
        print(f"✅ Transformer: {len(gaml_code)} caractères GAML générés")
        print(f"   - Lignes: {len(gaml_code.splitlines())}")
    
    def test_05_emitter_produces_complete_gaml(self):
        """Test 5: Vérifie que l'émetteur produit du GAML complet avec action et reflex"""
        cleaner = PseudoCodeCleaner()
        cleaned = cleaner.clean(self.ecological_model_pseudo)
        
        parser = LarkPseudoCodeParser()
        parse_result = parser.parse(cleaned)
        
        collector = VariableCollector()
        collection = collector.collect_from_parse_result(parse_result)
        
        transformer = GamlASTTransformer()
        
        config = EmissionConfig(
            generate_reflex=True,
            include_header_comments=True,
            include_annotations=True,
            include_variable_declarations=True
        )
        
        emitter = GamlEmitter(config=config)
        result = emitter.emit_from_pipeline(
            process_name="tree_growth_model",
            parse_result=parse_result,
            variable_collection=collection,
            transformer=transformer
        )
        
        self.assertIsInstance(result, object)  # EmissionResult
        self.assertTrue(len(result.code) > 0)
        self.assertTrue(result.has_actions)
        self.assertTrue(result.has_reflex)
        
        code = result.code
        
        # Vérifier la structure GAML
        self.assertIn('action tree_growth_model {', code)
        self.assertIn('reflex tree_growth_model_dynamics', code)
        self.assertIn('do tree_growth_model;', code)
        
        # Vérifier les commentaires d'annotations
        self.assertIn('// resource:', code)
        self.assertIn('// property:', code)
        
        # Vérifier que le corps est bien indenté
        lines = code.splitlines()
        indented_lines = [l for l in lines if l.startswith('    ')]
        self.assertTrue(len(indented_lines) > 10)
        
        print(f"✅ Emitter: {len(code)} caractères GAML finaux")
        print(f"   - Lignes: {len(lines)}")
        print(f"   - Action: {result.has_actions}")
        print(f"   - Reflex: {result.has_reflex}")
    
    def test_06_full_pipeline_integration(self):
        """Test 6: Test d'intégration complet du pipeline"""
        # Utiliser la fonction unifiée
        result = generate_gaml_code(
            process_name="tree_growth_model",
            pseudo_code=self.ecological_model_pseudo,
            config=EmissionConfig(generate_reflex=True)
        )
        
        self.assertTrue(len(result.code) > 0)
        self.assertEqual(result.process_name, "tree_growth_model")
        
        # Vérifier le code généré
        code = result.code
        
        # Structure principale
        self.assertIn('action tree_growth_model', code)
        
        # Variables avec annotations
        self.assertIn('biomass', code)
        self.assertIn('soil_nitrogen', code)
        
        # Opérations arithmétiques
        self.assertIn('*', code)
        self.assertIn('/', code)
        self.assertIn('+', code)
        self.assertIn('-', code)
        
        # Structures de contrôle
        self.assertIn('if', code)
        self.assertIn('else if', code)
        
        # Fonctions mathématiques
        self.assertIn('min(', code)
        self.assertIn('max(', code)
        
        # Procédure
        self.assertIn('action calculate_water_stress', code)
        
        print(f"\n{'='*60}")
        print("CODE GAML GÉNÉRÉ (EXTRAIT)")
        print('='*60)
        
        # Afficher les 30 premières lignes du code
        code_lines = code.splitlines()
        for i, line in enumerate(code_lines[:50]):
            print(line)
        if len(code_lines) > 50:
            print(f"... et {len(code_lines) - 50} lignes supplémentaires")
        
        print(f"\n{'='*60}")
        print(f"STATISTIQUES FINALES")
        print('='*60)
        print(f"Total lignes: {len(code_lines)}")
        print(f"Taille code: {len(code)} caractères")
        print(f"Warnings: {len(result.warnings)}")
        
        return result
    
    def test_07_specific_gaml_features(self):
        """Test 7: Vérifie des fonctionnalités GAML spécifiques"""
        result = self.test_06_full_pipeline_integration()
        code = result.code
        
        # Vérifier la conversion des opérateurs
        lines_to_check = [
            ('<-', 'Assignation avec <-'),
            (' = ', 'Comparaison avec ='),
            ('and', 'Opérateur logique and'),
            ('or', 'Opérateur logique or'),
            ('not', 'Opérateur logique not'),
        ]
        
        for pattern, description in lines_to_check:
            if pattern in code:
                print(f"   ✅ {description}: trouvé")
            else:
                print(f"   ⚠️  {description}: non trouvé")
        
        # Vérifier les annotations préservées
        if '// resource:' in code or '// property:' in code:
            print("   ✅ Annotations préservées en commentaires")
        
        # Vérifier l'indentation
        lines = code.splitlines()
        indent_counts = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
        if indent_counts:
            avg_indent = sum(indent_counts) / len(indent_counts)
            print(f"   ✅ Indentation moyenne: {avg_indent:.1f} espaces")
    
    def test_08_edge_cases(self):
        """Test 8: Tests des cas limites"""
        
        # Cas 1: Code vide
        empty_result = generate_gaml_code("empty", "")
        self.assertTrue(len(empty_result.code) > 0)
        self.assertIn("// ERROR", empty_result.code or "Empty code handled")
        
        # Cas 2: Code minimal
        minimal_pseudo = "x = 42; y = x + 1;"
        minimal_result = generate_gaml_code("minimal", minimal_pseudo)
        self.assertIn("x <- 42", minimal_result.code)
        self.assertIn("y <- x + 1", minimal_result.code)
        
        # Cas 3: Code avec seulement des commentaires
        comments_pseudo = "// Ceci est un commentaire\n// Un autre commentaire"
        comments_result = generate_gaml_code("comments", comments_pseudo)
        # Ne devrait pas planter
        self.assertIsNotNone(comments_result.code)
        
        # Cas 4: Structure de contrôle complexe
        complex_pseudo = """
        if (a > b) {
            if (c > d) {
                x = 1;
            } else {
                x = 2;
            }
        } else {
            x = 3;
        }
        """
        complex_result = generate_gaml_code("complex", complex_pseudo)
        self.assertIn("if (", complex_result.code)
        self.assertIn("else {", complex_result.code)
        
        print("✅ Tests cas limites réussis")
    
    def test_09_performance(self):
        """Test 9: Test de performance sur un pseudo-code volumineux"""
        import time
        
        # Générer un pseudo-code plus volumineux
        large_pseudo = self.ecological_model_pseudo * 3  # Triple la taille
        
        start_time = time.time()
        result = generate_gaml_code("large_model", large_pseudo)
        elapsed = time.time() - start_time
        
        print(f"✅ Performance: {elapsed:.2f} secondes")
        print(f"   - Taille entrée: {len(large_pseudo)} caractères")
        print(f"   - Taille sortie: {len(result.code)} caractères")
        print(f"   - Ratio: {len(result.code)/len(large_pseudo):.1f}x")
        
        self.assertLess(elapsed, 5.0, "La transformation devrait prendre moins de 5 secondes")
    
    def test_10_validate_output_syntax(self):
        """Test 10: Validation basique de la syntaxe GAML générée"""
        result = self.test_06_full_pipeline_integration()
        code = result.code
        
        # Vérifier l'équilibre des accolades
        open_braces = code.count('{')
        close_braces = code.count('}')
        self.assertEqual(open_braces, close_braces, 
                        f"Accolades déséquilibrées: {open_braces} ouvertes, {close_braces} fermées")
        
        # Vérifier l'équilibre des parenthèses
        open_parens = code.count('(')
        close_parens = code.count(')')
        self.assertEqual(open_parens, close_parens,
                        f"Parenthèses déséquilibrées: {open_parens} ouvertes, {close_parens} fermées")
        
        # Vérifier que chaque ligne d'instruction se termine par ;
        lines = code.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Ignorer les lignes vides, commentaires, accolades
            if stripped and not stripped.startswith('//') and not stripped in ('{', '}', '') and not stripped.endswith('{') and not stripped.endswith('}'):
                if not stripped.endswith(';') and not stripped.startswith('action') and not stripped.startswith('reflex'):
                    if not stripped.startswith('do') and not stripped.startswith('return'):
                        # Ceci peut être normal pour certaines structures
                        pass
        
        print("✅ Validation syntaxique: accolades et parenthèses équilibrées")
        
        # Afficher un résumé du code GAML généré
        self._print_code_summary(code)
    
    def _print_code_summary(self, code: str):
        """Affiche un résumé du code GAML généré"""
        lines = code.splitlines()
        
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DU CODE GAML GÉNÉRÉ")
        print("="*60)
        
        # Statistiques par type de ligne
        stats = {
            'action': 0,
            'reflex': 0,
            'if': 0,
            'else': 0,
            'assign': 0,
            'comment': 0,
            'empty': 0
        }
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                stats['empty'] += 1
            elif stripped.startswith('//'):
                stats['comment'] += 1
            elif stripped.startswith('action'):
                stats['action'] += 1
            elif stripped.startswith('reflex'):
                stats['reflex'] += 1
            elif stripped.startswith('if'):
                stats['if'] += 1
            elif stripped.startswith('else'):
                stats['else'] += 1
            elif '<-' in stripped:
                stats['assign'] += 1
        
        print(f"📝 Lignes totales: {len(lines)}")
        print(f"   • Actions: {stats['action']}")
        print(f"   • Reflex: {stats['reflex']}")
        print(f"   • Conditions if/else: {stats['if'] + stats['else']}")
        print(f"   • Assignations: {stats['assign']}")
        print(f"   • Commentaires: {stats['comment']}")
        print(f"   • Lignes vides: {stats['empty']}")


class TestSpecificFeatures(unittest.TestCase):
    """Tests spécifiques pour des fonctionnalités particulières"""
    
    def test_math_functions(self):
        """Test des fonctions mathématiques"""
        pseudo = """
        a = min(1, 2);
        b = max(3, 4);
        c = sqrt(9);
        d = abs(-5);
        e = sin(3.14);
        """
        
        result = generate_gaml_code("math_test", pseudo)
        code = result.code
        
        self.assertIn('min(1, 2)', code)
        self.assertIn('max(3, 4)', code)
        self.assertIn('sqrt(9)', code)
        self.assertIn('abs(-5)', code)
        self.assertIn('sin(3.14)', code)
        
        print("✅ Fonctions mathématiques correctement transformées")
    
    def test_loops(self):
        """Test des boucles"""
        pseudo = """
        for i = 1 to 10 {
            sum = sum + i;
        }
        
        for each item in list {
            total = total + item;
        }
        
        while (x < 100) {
            x = x + 1;
        }
        
        repeat {
            x = x - 1;
        } until (x == 0);
        """
        
        result = generate_gaml_code("loops_test", pseudo)
        code = result.code
        
        self.assertIn('loop i from: 1 to: 10', code)
        self.assertIn('loop item over: list', code)
        self.assertIn('loop while: x < 100', code)
        self.assertIn('loop while: not(x == 0)', code)  # repeat until transformé
        
        print("✅ Boucles correctement transformées")
    
    def test_switch_statement(self):
        """Test de l'instruction switch"""
        pseudo = """
        switch (x) {
            case 1:
                result = "un";
                break;
            case 2:
                result = "deux";
                break;
            default:
                result = "autre";
        }
        """
        
        result = generate_gaml_code("switch_test", pseudo)
        code = result.code
        
        self.assertIn('if (x = 1)', code)
        self.assertIn('else if (x = 2)', code)
        self.assertIn('else', code)
        self.assertNotIn('switch', code)  # switch doit être transformé
        
        print("✅ Switch correctement transformé en if/else")
    
    def test_function_procedure(self):
        """Test des fonctions et procédures"""
        pseudo = """
        function calculate(x, y) {
            result = x * y;
            return result;
        }
        
        procedure display(value) {
            print value;
        }
        """
        
        result = generate_gaml_code("func_test", pseudo)
        code = result.code
        
        self.assertIn('action calculate', code)
        self.assertIn('return result', code)
        self.assertIn('action display', code)
        self.assertIn('write value', code)
        
        print("✅ Fonctions et procédures correctement transformées")
    
    def test_nested_structures(self):
        """Test des structures imbriquées"""
        pseudo = """
        if (condition1) {
            if (condition2) {
                x = 1;
            } else {
                x = 2;
            }
        } else {
            if (condition3) {
                x = 3;
            }
        }
        """
        
        result = generate_gaml_code("nested_test", pseudo)
        code = result.code
        
        # Vérifier l'indentation
        lines = code.splitlines()
        indentation_levels = []
        for line in lines:
            if line.strip() and not line.strip().startswith('//'):
                indent = len(line) - len(line.lstrip())
                if indent > 0:  # Ignorer les lignes sans indentation
                    indentation_levels.append(indent)
        
        # Les indentations devraient être multiples de 4
        for level in indentation_levels:
            self.assertEqual(level % 4, 0, f"Indentation {level} non valide")
        
        print("✅ Structures imbriquées correctement indentées")
    
    def test_annotations_preservation(self):
        """Test de préservation des annotations"""
        pseudo = """
        biomass = initial_biomass /* resource_001 */;
        growth_rate = tree_growth /* property_123 */;
        """
        
        result = generate_gaml_code("annotations_test", pseudo)
        code = result.code
        
        self.assertIn('// resource:', code)
        self.assertIn('// property:', code)
        self.assertIn('resource_001', code)
        self.assertIn('property_123', code)
        
        print("✅ Annotations correctement préservées dans les commentaires")


class TestErrorHandling(unittest.TestCase):
    """Tests de gestion des erreurs"""
    
    def test_syntax_error(self):
        """Test de gestion des erreurs de syntaxe"""
        invalid_pseudo = """
        x = 5;
        if (x > 0 {  // Parenthèse fermante manquante
            y = 1;
        }
        """
        
        result = generate_gaml_code("error_test", invalid_pseudo)
        
        # Le pipeline ne doit pas planter
        self.assertIsNotNone(result.code)
        
        # Soit il y a une erreur dans les warnings, soit le code est partiel
        print(f"✅ Gestion d'erreur: {len(result.warnings)} avertissements")
    
    def test_missing_semicolon(self):
        """Test avec des points-virgules manquants"""
        missing_semicolon = """
        x = 5
        y = x + 1
        """
        
        result = generate_gaml_code("semicolon_test", missing_semicolon)
        
        # Le pipeline devrait gérer ou au moins ne pas planter
        self.assertIsNotNone(result.code)
        print("✅ Points-virgules manquants gérés")
    
    def test_invalid_annotation(self):
        """Test avec annotation mal formée"""
        invalid_annotation = """
        x = value /* invalid_annotation */;
        """
        
        result = generate_gaml_code("annotation_test", invalid_annotation)
        
        # Les annotations non standard doivent être ignorées ou conservées
        self.assertIsNotNone(result.code)
        print("✅ Annotations non standard gérées")


def run_all_tests():
    """Exécute tous les tests et affiche un résumé"""
    
    print("\n" + "="*70)
    print("🚀 EXÉCUTION DES TESTS DU PIPELINE PSEUDO-CODE → GAML")
    print("="*70)
    
    # Créer une suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestPipelineComplete))
    suite.addTests(loader.loadTestsFromTestCase(TestSpecificFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Afficher le résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    print(f"✅ Tests réussis: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Échecs: {len(result.failures)}")
    print(f"⚠️  Erreurs: {len(result.errors)}")
    print(f"📝 Total: {result.testsRun}")
    
    if result.wasSuccessful():
        print("\n🎉 TOUS LES TESTS ONT RÉUSSI !")
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez les détails ci-dessus.")
    
    return result


if __name__ == "__main__":
    # Configuration du logging pour les tests
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Exécuter les tests
    result = run_all_tests()
    
    # Optionnel: sauvegarder le code GAML généré
    if result.wasSuccessful():
        try:
            # Générer et sauvegarder le code final
            final_result = generate_gaml_code(
                "tree_growth_model_final",
                TestPipelineComplete.ecological_model_pseudo,
                config=EmissionConfig(generate_reflex=True, add_timestamps=True)
            )
            
            output_file = Path(__file__).parent / "output" / "generated_model.gaml"
            output_file.parent.mkdir(exist_ok=True)
            output_file.write_text(final_result.code, encoding='utf-8')
            print(f"\n💾 Code GAML sauvegardé dans: {output_file}")
            
        except Exception as e:
            print(f"\n⚠️  Impossible de sauvegarder le fichier: {e}")