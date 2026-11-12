# Cleaner → Lark Parser → VariableCollector → GamlASTTransformer → GamlEmitter
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from lark import Tree, Token

from src.gaml_generator.pseudocodeToaction.pseudocode_cleaner import Annotation
from src.gaml_generator.pseudocodeToaction.lark_parser import ParseResult


@dataclass
class VariableInfo:
    name: str
    scope_level: int
    is_parameter: bool = False
    annotations: List[Annotation] = field(default_factory=list)
    first_use_line: Optional[int] = None
    defined_in_function: Optional[str] = None
    
    def add_annotation(self, annotation: Annotation):
        if annotation not in self.annotations:
            self.annotations.append(annotation)


@dataclass
class FunctionInfo:
    name: str
    type: str
    parameters: List[str] = field(default_factory=list)
    scope_level: int = 0
    annotations: List[Annotation] = field(default_factory=list)


@dataclass
class CollectionResult:
    variables: Dict[str, VariableInfo] = field(default_factory=dict)
    functions: Dict[str, FunctionInfo] = field(default_factory=dict)
    global_variables: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_variable(self, name: str) -> Optional[VariableInfo]:
        return self.variables.get(name)
    
    def get_annotations_for(self, name: str) -> List[Annotation]:
        var = self.variables.get(name)
        return var.annotations if var else []
    
    def to_dict(self) -> dict:
        return {
            'variables': {k: vars(v) for k, v in self.variables.items()},
            'functions': {k: vars(v) for k, v in self.functions.items()},
            'global_variables': self.global_variables,
            'warnings': self.warnings
        }


class VariableCollector:
    """
    Collecteur robuste de variables depuis l'AST.
    - Gestion correcte des numéros de ligne
    - Association fiable annotations → variables
    - Scope local/global correctement géré
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        self.scope_stack: List[set] = [set()]                    # scope global
        self.variables: Dict[str, VariableInfo] = {}
        self.functions: Dict[str, FunctionInfo] = {}
        
        self.current_function: Optional[str] = None
        self.line_counter: int = 0
        self.annotations_map: Dict[int, List[Annotation]] = {}   # ligne → annotations

    def enter_scope(self):
        self.scope_stack.append(set())
        self.logger.debug(f"Entrée scope niveau {len(self.scope_stack)-1}")

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
            self.logger.debug(f"Sortie scope, niveau actuel {len(self.scope_stack)-1}")

    @property
    def current_scope(self) -> set:
        return self.scope_stack[-1]

    def add_annotation(self, annotation: Annotation):
        """Ajoute une annotation à la ligne courante"""
        if self.line_counter not in self.annotations_map:
            self.annotations_map[self.line_counter] = []
        self.annotations_map[self.line_counter].append(annotation)
        self.logger.debug(f"Annotation ajoutée ligne {self.line_counter}: {annotation.value}")

    def record_variable_use(self, name: str, is_parameter: bool = False):
        if not name:
            return

        if name in self.variables:
            var_info = self.variables[name]
            if is_parameter and not var_info.is_parameter:
                var_info.is_parameter = True
        else:
            var_info = VariableInfo(
                name=name,
                scope_level=len(self.scope_stack) - 1,
                is_parameter=is_parameter,
                first_use_line=self.line_counter,
                defined_in_function=self.current_function
            )
            self.variables[name] = var_info
            self.logger.info(f"VARIABLE DÉTECTÉE : {name} (scope_level={var_info.scope_level}, ligne={self.line_counter})")

        self.current_scope.add(name)

        # Associer les annotations de la ligne courante
        if self.line_counter in self.annotations_map:
            for ann in self.annotations_map[self.line_counter]:
                var_info.add_annotation(ann)
                self.logger.debug(f"Annotation '{ann.value}' liée à {name}")

    def collect_from_parse_result(self, parse_result: ParseResult) -> CollectionResult:
        if not parse_result.success:
            self.logger.warning("Collecte sur parsing échoué")
            return CollectionResult(warnings=["Parsing échoué"])

        # Charger annotations du cleaner
        if 'annotations' in parse_result.metadata:
            for ann in parse_result.metadata.get('annotations', []):
                self.add_annotation(ann)

        self.line_counter = 0
        self._traverse(parse_result.tree)

        result = CollectionResult(
            variables=self.variables,
            functions=self.functions,
            global_variables=list(self.scope_stack[0]),
            warnings=[]
        )

        self.logger.info(f"Collecte terminée : {len(self.variables)} variables, {len(self.functions)} fonctions")
        return result

    def _traverse(self, node: Tree):
        if not isinstance(node, Tree):
            return

        node_type = node.data
        self.line_counter += 1   # Incrémentation par nœud (plus précis qu'avant)

        # === ASSIGNATION ===
        if node_type == 'assign_stmt':
            # Variable à gauche
            if node.children and isinstance(node.children[0], Tree) and node.children[0].data == 'var_name':
                var_token = self._get_token_from_var_name(node.children[0])
                if var_token:
                    self.record_variable_use(var_token.value)

            # Expression de droite
            for child in node.children[1:]:
                if isinstance(child, Tree):
                    self._traverse(child)
            return

        # === FOR EACH ===
        elif node_type == 'for_each_stmt':
            self.enter_scope()
            if node.children and isinstance(node.children[0], Tree) and node.children[0].data == 'var_name':
                var_token = self._get_token_from_var_name(node.children[0])
                if var_token:
                    self.record_variable_use(var_token.value)
            for child in node.children[1:]:
                if isinstance(child, Tree):
                    self._traverse(child)
            self.exit_scope()
            return

        # === FOR RANGE ===
        elif node_type == 'for_range_stmt':
            self.enter_scope()
            if node.children and isinstance(node.children[0], Tree) and node.children[0].data == 'var_name':
                var_token = self._get_token_from_var_name(node.children[0])
                if var_token:
                    self.record_variable_use(var_token.value)
            for child in node.children[1:]:
                if isinstance(child, Tree):
                    self._traverse(child)
            self.exit_scope()
            return

        # === BLOCS AVEC NOUVEAU SCOPE ===
        elif node_type in ('if_stmt', 'else_if', 'else_block', 'while_stmt', 'switch_stmt'):
            self.enter_scope()
            for child in node.children:
                if isinstance(child, Tree):
                    self._traverse(child)
            self.exit_scope()
            return

        # === FONCTIONS / PROCÉDURES ===
        elif node_type in ('procedure_decl', 'function_decl'):
            func_name = None
            for child in node.children:
                if isinstance(child, Token) and child.type in ('ID', 'CNAME'):
                    func_name = child.value
                    break

            if func_name:
                self.functions[func_name] = FunctionInfo(name=func_name, type='function' if node_type == 'function_decl' else 'procedure')
                self.current_function = func_name

            self.enter_scope()

            for child in node.children:
                if isinstance(child, Tree):
                    if child.data == 'var_name':
                        var_token = self._get_token_from_var_name(child)
                        if var_token:
                            self.record_variable_use(var_token.value, is_parameter=True)
                            if func_name in self.functions:
                                self.functions[func_name].parameters.append(var_token.value)
                    else:
                        self._traverse(child)

            self.exit_scope()
            self.current_function = None
            return

        # === VAR_NAME isolé ===
        elif node_type == 'var_name':
            var_token = self._get_token_from_var_name(node)
            if var_token:
                self.record_variable_use(var_token.value)
            return

        # Récursion par défaut
        for child in node.children:
            if isinstance(child, Tree):
                self._traverse(child)

    def _get_token_from_var_name(self, var_node: Tree) -> Optional[Token]:
        """Récupère le Token ID ou CNAME de manière robuste"""
        if not isinstance(var_node, Tree) or var_node.data != 'var_name':
            return None
        for child in var_node.children:
            if isinstance(child, Token) and child.type in ('ID', 'CNAME'):
                return child
        return None


def print_variable_summary(result: CollectionResult):
    print(f"\n📊 RÉSUMÉ DE LA COLLECTE")
    print("="*60)
    
    print(f"\n📦 Variables globales ({len(result.global_variables)}):")
    for var in sorted(result.global_variables):
        info = result.get_variable(var)
        ann = f" [{', '.join(a.value for a in info.annotations)}]" if info and info.annotations else ""
        print(f"  • {var}{ann}")
    
    annotated = [v for v in result.variables.values() if v.annotations]
    if annotated:
        print(f"\n🏷️ Variables avec annotations ({len(annotated)}):")
        for v in annotated:
            anns = ', '.join(a.value for a in v.annotations)
            print(f"  • {v.name}: {anns}")
    
    print("="*60)