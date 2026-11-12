# Cleaner → Lark Parser → VariableCollector → GamlASTTransformer → GamlEmitter
import logging
from typing import Optional, Union, List, Dict, Any
from dataclasses import dataclass, field
import sys
import os
import re
from pathlib import Path
import time
from lark import Lark, ParseError, Tree, UnexpectedInput

# Ajout du chemin pour importer les modules du pipeline
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Réutilisation du CleanedCode du cleaner
from src.gaml_generator.pseudocodeToaction.pseudocode_cleaner import CleanedCode

@dataclass
class ParseResult:
    """Résultat complet du parsing avec métadonnées"""
    tree: Tree
    success: bool
    parse_time: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    original_code: str = ""
    cleaned_code: str = ""
    
    def is_valid(self) -> bool:
        """L'AST est-il utilisable pour la suite ?"""
        return self.success and len(self.errors) == 0
    
    def get_stats(self) -> Dict[str, int]:
        """Retourne des statistiques sur l'AST"""
        stats = {}
        def count_nodes(node):
            if hasattr(node, 'data'):
                stats[node.data] = stats.get(node.data, 0) + 1
                for child in node.children:
                    if isinstance(child, Tree):
                        count_nodes(child)
        count_nodes(self.tree)
        return stats
    
    def pretty_print(self) -> str:
        """Retourne une représentation lisible de l'AST"""
        lines = []
        lines.append(f"Parsing {'réussi' if self.success else 'échoué'} en {self.parse_time:.3f}s")
        
        if self.warnings:
            lines.append(f"{len(self.warnings)} avertissement(s):")
            for w in self.warnings[:5]:
                lines.append(f"   - {w}")
        
        if self.errors:
            lines.append(f"{len(self.errors)} erreur(s):")
            for e in self.errors[:5]:
                lines.append(f"   - {e}")
        
        stats = self.get_stats()
        if stats:
            lines.append("Statistiques AST:")
            for stmt_type, count in sorted(stats.items()):
                lines.append(f"   - {stmt_type}: {count}")
        
        return "\n".join(lines)


class ParseErrorFormatter:
    @staticmethod
    def format_error(exc: UnexpectedInput, code: str) -> str:
        line = getattr(exc, 'line', None)
        col = getattr(exc, 'column', None)
        lines = code.splitlines()
        snippet = lines[line-1] if line and line-1 < len(lines) else ""
        token = getattr(exc, 'token', '?')
        expected = getattr(exc, 'expected', [])
        
        if line and col and snippet:
            return (
                f"Erreur de syntaxe à la ligne {line}, colonne {col}\n"
                f"   → {snippet}\n"
                f"     {' ' * (col-1)}^\n"
                f"   Jeton inattendu : '{token}'\n"
                f"   Attendu : {', '.join(sorted(expected)) if expected else 'rien'}"
            )
        else:
            return f"Erreur inattendue : {str(exc)}"


class ASTValidator:
    @staticmethod
    def validate(tree: Tree) -> List[str]:
        warnings = []
        if tree.data != 'start':
            warnings.append(f"Racine de l'AST inattendue: {tree.data}, attendu 'start'")
        return warnings


class LarkPseudoCodeParser:
    def __init__(self, 
                 grammar: Optional[Union[str, Path]] = None,
                 grammar_str: Optional[str] = None,
                 logger: Optional[logging.Logger] = None,
                 parser_type: str = 'earley',
                 debug: bool = False,
                 strict: bool = True):
        self.logger = logger or logging.getLogger(__name__)
        self.debug = debug
        self.strict = strict
        self.parser_type = parser_type
        self.last_error: Optional[Exception] = None
        self.validator = ASTValidator()

        grammar_source = self._load_grammar(grammar, grammar_str)
        
        try:
            if parser_type == 'earley':
                self.parser = Lark(
                    grammar_source,
                    start='start',
                    parser='earley',
                    lexer='dynamic',
                    ambiguity='explicit',
                    propagate_positions=True,
                    debug=self.debug
                )
            else:
                self.parser = Lark(
                    grammar_source,
                    start='start',
                    parser='lalr',
                    lexer='basic',   
                    propagate_positions=True,
                    maybe_placeholders=False,
                    debug=self.debug
                )

            self.logger.info(f"✅ Grammaire chargée (parser={parser_type})")
        except Exception as e:
            raise RuntimeError(f"Erreur d'initialisation du parser: {e}")

    def _load_grammar(self, grammar: Optional[Union[str, Path]], grammar_str: Optional[str]) -> str:
        if grammar_str:
            return grammar_str
        if grammar:
            grammar_path = Path(grammar)
        else:
            grammar_path = Path(__file__).parent / "pseudocode.lark"
        
        try:
            with open(grammar_path, 'r', encoding='utf-8') as f:
                grammar_source = f.read()
            return grammar_source
        except FileNotFoundError:
            raise FileNotFoundError(f"Fichier de grammaire introuvable: {grammar_path}")
        except Exception as e:
            raise RuntimeError(f"Erreur de chargement: {e}")

    def parse(self, cleaned: Union[str, CleanedCode], original_code: Optional[str] = None) -> ParseResult:
        start_time = time.time()

        if isinstance(cleaned, CleanedCode):
            code = cleaned.code
            metadata = {'cleaner_warnings': cleaned.warnings, 'annotations': cleaned.annotations, 'statistics': cleaned.statistics}
            original = original_code or cleaned.code
        else:
            code = cleaned
            metadata = {}
            original = original_code or code

        result = ParseResult(
            tree=Tree('start', []),
            success=False,
            parse_time=0,
            metadata=metadata,
            original_code=original,
            cleaned_code=code
        )

        try:
            ast = self.parser.parse(code)
            #ast = self._resolve_annotation_ambiguities(ast)
            ast = self._resolve_annotation_nodes(ast)
            elapsed = time.time() - start_time

            validation_warnings = self.validator.validate(ast)

            result.tree = ast
            result.success = True
            result.parse_time = elapsed
            result.warnings.extend(validation_warnings)

            stats = result.get_stats()
            self.logger.info(f"Parsing réussi en {elapsed:.3f}s, {sum(stats.values())} nœuds")

            if validation_warnings:
                for w in validation_warnings:
                    self.logger.warning(f"Validation AST: {w}")

            if self.debug:
                self.logger.debug(ast.pretty())

        except UnexpectedInput as e:
            self.last_error = e
            formatted = ParseErrorFormatter.format_error(e, code)
            result.parse_time = time.time() - start_time
            result.errors.append(formatted)
            if self.strict:
                raise
            else:
                self.logger.warning(formatted)
        except Exception as e:
            self.last_error = e
            msg = f"Erreur inattendue: {e}"
            result.parse_time = time.time() - start_time
            result.errors.append(msg)
            if self.strict:
                raise
            else:
                self.logger.warning(msg)

        return result
    

    def _resolve_annotation_nodes(self, tree: Tree) -> Tree:
        """
        Résolution robuste des ambiguïtés liées aux annotations.
        On priorise systématiquement les assign_stmt qui contiennent une annotation.
        """
        def transform(node):
            if isinstance(node, Tree):
                if node.data == "_ambig":
                    # Cherche d'abord un assign_stmt avec annotation
                    for child in node.children:
                        if isinstance(child, Tree) and child.data == "assign_stmt":
                            # Vérifie s'il contient une annotation
                            has_annotation = any(
                                isinstance(c, Tree) and c.data == "annotation" 
                                for c in child.children
                            )
                            if has_annotation:
                                return child
                    
                    # Sinon, on prend le premier assign_stmt valide
                    for child in node.children:
                        if isinstance(child, Tree) and child.data == "assign_stmt":
                            return child
                    
                    # Sinon, on prend le premier enfant valide
                    return node.children[0] if node.children else node
                
                # Récursion sur les enfants
                node.children = [transform(c) for c in node.children]
            return node

        return transform(tree)
    
    def _resolve_annotation_nodes(self, tree: Tree) -> Tree:
        """
        Résout les ambiguïtés liées aux annotations dans l'AST.
        Si un nœud '_ambig' contient plusieurs 'annotation', on garde la première.
        """
        def transform(node):
            if isinstance(node, Tree):
                if node.data == "_ambig":
                    # Priorité aux assign_stmt bien formés
                    for c in node.children:
                        if isinstance(c, Tree) and c.data == "assign_stmt":
                            return c
                    return node.children[0]
                node.children = [transform(c) for c in node.children]
            return node
        return transform(tree)

