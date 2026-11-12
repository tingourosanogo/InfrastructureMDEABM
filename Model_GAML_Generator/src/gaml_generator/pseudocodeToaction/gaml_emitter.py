"""
GamlEmitter - Version finale intégrée au pipeline complet
Pipeline: Cleaner → Lark Parser → VariableCollector → GamlASTTransformer → GamlEmitter
"""

import logging
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

# Imports des composants précédents du pipeline
from .pseudocode_cleaner import PseudoCodeCleaner, CleanedCode
from .lark_parser import LarkPseudoCodeParser, ParseResult
from .variable_collector import VariableCollector, CollectionResult
from .gaml_ast_transformer import GamlASTTransformer


@dataclass
class EmissionConfig:
    """Configuration d'émission GAML"""
    indent_size: int = 4
    generate_reflex: bool = True
    reflex_suffix: str = "_dynamics"
    include_header_comments: bool = True
    minify: bool = False


@dataclass
class EmissionResult:
    """Résultat complet de l'émission"""
    code: str
    process_name: str
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GamlEmitter:
    """
    Émetteur GAML complet et intégré.
    - Méthode haut-niveau : accepte directement le pseudo-code brut
    - Méthode bas-niveau : accepte le corps déjà transformé (pour tests ou usage avancé)
    """

    def __init__(self, logger: Optional[logging.Logger] = None, config: Optional[EmissionConfig] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.config = config or EmissionConfig()

    # ===================================================================
    # MÉTHODE HAUT-NIVEAU (pipeline complet)
    # ===================================================================
    def generate_from_pseudo_code(
        self,
        process_name: str,
        pseudo_code: str,
        equation: Optional[str] = None,
        description: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
    ) -> EmissionResult:
        """
        Méthode principale : prend le pseudo-code brut et exécute tout le pipeline.
        """
        warnings = []

        try:

            # Debug initial du pseudo-code brut
            print("-" * 30 + "=== PSEUDO-CODE BRUT DEBUG ===" + "-" * 30) 
            print(f"Vérifier -> Corps brut pour '{process_name}': \n")
            for bl in pseudo_code.splitlines():
                print(bl)
            

            # 1. Cleaner
            cleaner = PseudoCodeCleaner(logger=self.logger)
            cleaned: CleanedCode = cleaner.clean(pseudo_code)

            # Debug après nettoyage
            print("-" * 33 + " === CLEANER DEBUG === " + "-" * 33 + "\n" + "Etape 1 - Nettoyage du pseudo-code terminé")
            print(f"Vérifier -> Corps néttoyé pour '{process_name}': \n")
            for bl in cleaned.code.splitlines():
                print(bl) 
            
            if not cleaned.code.strip():
                warnings.append("Code nettoyé vide après nettoyage")
                print(f"  → Code nettoyé vide pour '{process_name}' \n  → Erreur potentielle dans le nettoyage ou code d'entrée vide \n → Vérifiez les annotations et le format du pseudo-code d'entrée.")
                print(f"  → Code d'entrée original :\n{pseudo_code}")
                print(f"  → Code nettoyé :\n{cleaned.code}")
                print("-" * 90)
                return self._empty_result(process_name, warnings)

            # 2. Parser
            parser = LarkPseudoCodeParser(logger=self.logger)
            parse_result: ParseResult = parser.parse(cleaned)

            # Debug après parsing
            print("-" * 34 + " === PARSER DEBUG === " + "-" * 34)
            print(f"Etape 2 - Parsing Lark OK \nVérifier -> AST à traduire pour '{process_name}':\n")
            if parse_result.is_valid():
                #print("Etape 2 - Parsing Lark OK")
                print(f"  AST généré : {parse_result.pretty_print()}") 
            else:
                print("  → Parsing échoué")

            if not parse_result.success:
                warnings.extend(parse_result.errors)
                return self._empty_result(process_name, warnings)

            # 3. Variable Collector
            collector = VariableCollector(logger=self.logger)
            collection: CollectionResult = collector.collect_from_parse_result(parse_result)

            # Debug après collecte de variables
            print("-" * 30 + "=== VARIABLE COLLECTOR DEBUG ===" + "-" * 30)
            print(f"Etape 3 - Collecte de variables OK \nVérifier -> Variables collectées pour '{process_name}': \n")
            if collection.variables:
                print(f"{len(collection.variables)} variables trouvées : \n {', '.join(collection.variables)} \n")
             

            # 4. Transformer
            transformer = GamlASTTransformer(logger=self.logger)
            translated_body: str = transformer.transform(parse_result, collection)

            if not translated_body.strip():
                warnings.append("Corps traduit vide après transformation AST → GAML")
                print(f"  → Corps traduit vide pour '{process_name}' \n  → Erreur potentielle dans la transformation ou code d'entrée non reconnu \n → Vérifiez les étapes précédentes et le format du pseudo-code d'entrée.")
                print(f"  → Code d'entrée original :\n{pseudo_code}")
                print(f"  → Code traduit :\n{translated_body}")
                return self._empty_result(process_name, warnings)

            # Debug après transformation
            print("-" * 31 + " === GAML TRANSFORMER DEBUG === " + "-" * 31)
            #print(f"\nEtape 4 - Transformation AST → GAML terminée")
            print(f"Etape 4 - Transformation AST -> GAML terminée \nVérifier -> Corps traduit pour '{process_name}':\n")
            for bl in translated_body.splitlines(): 
                print(f"  {bl}") 

            
            # 5. Déclarations (commentées, car le pipeline principal les gérera plus tard)
            declarations = []  # Pour l'instant vide → sera fourni par le pipeline général

            # 6. Émission finale (bas-niveau)
            result = self.emit(
                process_name=process_name,
                declarations=declarations,
                translated_body=translated_body,
                equation=equation,
                description=description,
                depends_on=depends_on,
            )

            result.warnings.extend(warnings)
            return result

        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution du pipeline complet: {e}")
            warnings.append(f"Exception pipeline: {str(e)}")
            return self._empty_result(process_name, warnings)

    # ===================================================================
    # MÉTHODE BAS-NIVEAU (utilisée par generate_from_pseudo_code)
    # ===================================================================
    
    def _indent_line(self, text: str, level: int = 1) -> str:
        """Applique l'indentation configurée à une ligne unique."""        
        return (" " * self.config.indent_size * level) + text

    def _indent_block(self, text: str, level: int = 0) -> List[str]:
        """Prend un bloc de texte multi-lignes et indente chaque ligne proprement."""
        if not text: return []
        lines = [line.strip() for line in text.splitlines()]
        return [self._indent_line(line, level) for line in lines if line]

    
    def emit(self, process_name: str, declarations: List[str], translated_body: str, 
            equation: Optional[str] = None, description: Optional[str] = None, 
            depends_on: Optional[List[str]] = None) -> EmissionResult:
        
        normalized_name = self._normalize_name(process_name)
        lines: List[str] = []
        warnings = []

        # --- 1. En-tête (Level 1 -> 4 espèces) ---
        if self.config.include_header_comments:
            lines.append(self._indent_line("// " + "="*44, 1))
            lines.append(self._indent_line(f"// Action: {normalized_name}", 1))
            if description: lines.append(self._indent_line(f"// Description: {description.strip()}", 1))
            if equation: lines.append(self._indent_line(f"// Equation: {equation.strip()}", 1))
            if depends_on: lines.append(self._indent_line(f"// Depends on: {', '.join(depends_on)}", 1))
            lines.append(self._indent_line("// " + "="*44, 1))

        # --- 2. Début de l'action (Level 1 -> 4 espèces) ---
        lines.append(self._indent_line(f"action {normalized_name} {{", 1))

        # --- 3. Contenu de l'action (Level 1 -> 8 espèces) ---
        # Déclarations locales
        if declarations:
            indent = " " * self.config.indent_size * 2
            lines.append(indent + "// Déclarations locales")
            for decl in declarations:
                lines.append(indent + decl.strip())
            lines.append("")

        # Corps (Level 2 -> 8 espèces)
        body_lines = [line.rstrip() for line in translated_body.splitlines() if line.strip()]
        if body_lines:
            indent = " " * self.config.indent_size * 2
            for line in body_lines:
                lines.append(indent + line)
        else:
            indent = " " * self.config.indent_size * 2
            lines.append(indent + "// TODO: Corps du processus vide ou non traduit")
            warnings.append(f"Corps traduit vide pour '{process_name}'")

        # --- 4. Fin de l'action (Level 1 -> 4 espèces) ---
        lines.append(self._indent_line("}", 1))

        # --- 5. Reflex (Level 1 -> 4 espèces) ---
        if self.config.generate_reflex:
            indent = " " * self.config.indent_size * 1
            lines.append("\n" + indent + "// Reflex associé pour les dynamiques continues")
            lines.append(indent + f"reflex {normalized_name}_reflex {{")
            lines.append(self._indent_line(f"do {normalized_name};", 2))
            lines.append(indent + "}")

        return EmissionResult(
            code="\n".join(lines),
            process_name=normalized_name,
            warnings=warnings,
            metadata={"body_length": len(translated_body)}
        )


    def _normalize_name(self, name: str) -> str:
        """Normalise le nom selon les règles GAML"""
        if not name:
            return ""
        normalized = re.sub(r'[^a-zA-Z0-9_]', '_', name.strip())
        if normalized and normalized[0].isdigit():
            normalized = "_" + normalized
        normalized = re.sub(r'_+', '_', normalized)
        return normalized.lower()

    def _finalize_code(self, code: str) -> str:
        """Nettoyage final"""
        if self.config.minify:
            code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'\s+', ' ', code)
        else:
            code = re.sub(r'\n{3,}', '\n\n', code)
            code = re.sub(r' +$', '', code, flags=re.MULTILINE)
        return code.strip() + "\n"

    def _empty_result(self, process_name: str, warnings: List[str]) -> EmissionResult:
        """Résultat en cas d'erreur"""
        return EmissionResult(
            code=f"// ERROR: Pipeline failed for {process_name}\n",
            process_name=process_name,
            warnings=warnings
        )


# Méthode de convenance pour usage rapide
def quick_generate_gaml(process_name: str, pseudo_code: str) -> str:
    emitter = GamlEmitter()
    result = emitter.generate_from_pseudo_code(process_name, pseudo_code)
    return result.code