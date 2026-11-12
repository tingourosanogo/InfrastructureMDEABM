"""
GamlASTTransformer - Version FINALE (corrigée pour assign_op Tree)
Pipeline: Cleaner → Lark Parser → VariableCollector → GamlASTTransformer → GamlEmitter
"""

from lark import Tree, Token
import logging
from typing import List, Union, Optional
from dataclasses import dataclass

from src.gaml_generator.pseudocodeToaction.pseudocode_cleaner import Annotation
from src.gaml_generator.pseudocodeToaction.lark_parser import ParseResult
from src.gaml_generator.pseudocodeToaction.variable_collector import CollectionResult


@dataclass
class TransformationContext:
    parse_result: ParseResult
    variable_collection: CollectionResult
    indent_size: int = 4
    current_indent: int = 0
    in_function: bool = False
    current_function: Optional[str] = None

    def indent(self) -> str:
        return " " * (self.current_indent * self.indent_size)

    def increase_indent(self):
        self.current_indent += 1

    def decrease_indent(self):
        self.current_indent -= 1


class GamlASTTransformer:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

        self.assign_operator_map = {
            '+=': '+=', '-=': '-=', '*=': '*=', '/=': '/=', '=': '<-'
        }
        self.compare_operator_map = {
            '==': '=', '!=': '!=', '>=': '>=', '<=': '<=', '>': '>', '<': '<'
        }
        self.arithmetic_operator_map = {'+': '+', '-': '-', '*': '*', '/': '/', '^': '^'}
        self.logic_operator_map = {'and': 'and', 'or': 'or', 'AND': 'and', 'OR': 'or', '&&': 'and', '||': 'or', '!': 'not', 'NOT': 'not'}

    # ===================================================================
    # HANDLERS SPÉCIAUX
    # ===================================================================
    def atom(self, children: List, ctx: TransformationContext) -> str:
        return self._transform_node(children[0], ctx) if children else ""

    def _ambig(self, children: List, ctx: TransformationContext) -> str:
        for child in children:
            if isinstance(child, Tree) and child.data != "_ambig":
                return self._transform_node(child, ctx)
        return self._transform_node(children[0], ctx) if children else ""

    def assign_op(self, children: List, ctx: TransformationContext) -> str:
        """NOUVEAU : descend dans la règle assign_op pour récupérer le vrai opérateur"""
        if children and isinstance(children[0], Token):
            return children[0].value
        return "="  # fallback

    # ===================================================================
    # OPÉRATEURS & ASSIGNATION (CORRIGÉE)
    # ===================================================================
    def _to_gaml_operator(self, op: Union[str, Token, Tree], assign: bool = False) -> str:
        if isinstance(op, Tree):
            op = self._transform_node(op, None)
        if isinstance(op, Token):
            op = op.value
        op_lower = str(op).lower().strip()

        if assign:
            return self.assign_operator_map.get(op_lower, op_lower)
        if op_lower in self.compare_operator_map:
            return self.compare_operator_map[op_lower]
        if op_lower in self.arithmetic_operator_map:
            return self.arithmetic_operator_map[op_lower]
        if op_lower in self.logic_operator_map:
            return self.logic_operator_map[op_lower]
        return op_lower

    def assign_stmt(self, children: List, ctx: TransformationContext) -> str:
        """Gestion robuste de tous les cas d'assignation (avec ou sans annotation avant/après opérateur)"""
        if not children:
            return ""

        var_name = self._transform_node(children[0], ctx)

        # Cas très simple : "var;"
        if len(children) == 1:
            return f"{var_name};"

        # On cherche l'opérateur et l'expression en ignorant les annotations intermédiaires
        op_idx = None
        expr_idx = None
        ann_idx = None

        for i, child in enumerate(children):
            if isinstance(child, Tree):
                if child.data == 'assign_op':
                    op_idx = i
                elif child.data == 'expr':
                    expr_idx = i
                elif child.data == 'annotation':
                    ann_idx = i

        if op_idx is None or expr_idx is None:
            # Fallback (cas sans opérateur)
            return f"{var_name};"

        gaml_op = self._to_gaml_operator(children[op_idx], assign=True)
        expr_part = self._transform_node(children[expr_idx], ctx)

        line = f"{var_name} {gaml_op} {expr_part}"
        line += ";"
        
        # Ajout de l'annotation (peu importe sa position)
        if ann_idx is not None:
            ann = self._transform_node(children[ann_idx], ctx)
            if ann:
                line += f" {ann}"

        
        return line

    def annotation(self, children: List, ctx: TransformationContext) -> str:
        if not children:
            return ""
        child = children[0]
        value = child.value if isinstance(child, Token) else str(child)

        if "resource_" in value:
            return f"// resource {value}"
        elif "property_" in value:
            return f"// property {value}"
        return f"// {value}"

    # ===================================================================
    # TRANSFORMATION PRINCIPALE
    # ===================================================================
    def transform(self, parse_result: ParseResult, variable_collection: CollectionResult) -> str:
        if not parse_result.success:
            return "// ERROR: parsing failed"

        ctx = TransformationContext(parse_result=parse_result, variable_collection=variable_collection)
        result = self._transform_node(parse_result.tree, ctx)
        lines = self._to_lines(result)

        header = self._generate_header(variable_collection)
        return (header + "\n" + "\n".join(lines)) if header else "\n".join(lines)

    def _generate_header(self, collection: CollectionResult) -> str:
        lines = []
        annotated = [v for v in collection.variables.values() if v.annotations]
        if annotated:
            lines.extend([
                "// =============================================",
                "// VARIABLES AVEC ANNOTATIONS (resources/properties)",
                "// ============================================="
            ])
            for var in annotated:
                for ann in var.annotations:
                    lines.append(f"// {var.name}: {ann.value}")
            lines.append("")

        if collection.functions:
            lines.extend([
                "// =============================================",
                "// FONCTIONS ET PROCÉDURES",
                "// ============================================="
            ])
        return "\n".join(lines)

    # ===================================================================
    # MÉTHODES GÉNÉRIQUES
    # ===================================================================
    def _transform_node(self, node: Union[Tree, Token], ctx: TransformationContext):
        if isinstance(node, Tree):
            return self._transform_tree(node, ctx)
        elif isinstance(node, Token):
            return self._transform_token(node, ctx)
        return str(node)

    def _transform_tree(self, tree: Tree, ctx: TransformationContext):
        method_name = tree.data

        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(tree.children, ctx)

        # Règles intermédiaires d'expression → descente automatique
        if method_name in {'logic_or', 'logic_and', 'equality', 'comparison',
                           'term', 'factor', 'power', 'unary', 'primary', 'expr'}:
            return self._transform_node(tree.children[0], ctx) if tree.children else ""

        self.logger.warning(f"Règle non gérée: {method_name}")
        return f"// [UNHANDLED: {method_name}]"

    def _transform_token(self, token: Token, ctx: TransformationContext) -> str:
        if token.type == 'BOOL':
            return token.value.lower()
        return token.value

    def _to_lines(self, item) -> List[str]:
        if isinstance(item, str):
            return [item] if item.strip() else []
        if isinstance(item, list):
            lines = []
            for sub in item:
                lines.extend(self._to_lines(sub))
            return lines
        return [str(item)] if str(item).strip() else []

    # ===================================================================
    # EXPRESSIONS (robuste)
    # ===================================================================
    def expr(self, children: List, ctx: TransformationContext) -> str:
        if not children:
            return ""
        if len(children) == 1:
            return self._transform_node(children[0], ctx)

        # Parenthèses explicites
        if (len(children) == 3 and
            isinstance(children[0], Token) and children[0].value == '(' and
            isinstance(children[2], Token) and children[2].value == ')'):
            return f"({self._transform_node(children[1], ctx)})"

        # Opérateur binaire
        if len(children) == 3:
            left = self._transform_node(children[0], ctx)
            op = self._transform_node(children[1], ctx)
            right = self._transform_node(children[2], ctx)
            return f"{left} {op} {right}"

        return " ".join(self._transform_node(c, ctx) for c in children)

    def var_name(self, children: List, ctx: TransformationContext) -> str:
        if children and isinstance(children[0], Token):
            return children[0].value
        return ""

    def func_call(self, children: List, ctx: TransformationContext) -> str:
        # 1. Identifier le nom de la fonction (premier enfant)
        func_name = self._transform_node(children[0], ctx)
        
        # 2. Vérifier si le dernier élément est le point-virgule (Token SEMI)
        # On regarde si le dernier enfant est un objet Token et si sa valeur est ";"
        has_semi = False
        if children and hasattr(children[-1], 'value') and children[-1].value == ';':
            has_semi = True
            # On retire le point-virgule de la liste des arguments potentiels
            args_pool = children[1:-1]
        else:
            args_pool = children[1:]

        # 3. Transformer uniquement les arguments restants
        args = [self._transform_node(arg, ctx) for arg in args_pool]
        
        # 4. Construire la chaîne : le ";" est placé à l'extérieur des parenthèses
        result = f"{func_name}({', '.join(filter(None, args))})"
        return f"{result};" if has_semi else result



    def list_literal(self, children: List, ctx: TransformationContext) -> str:
        items = [self._transform_node(c, ctx) for c in children]
        return f"[{', '.join(items)}]"

    # ===================================================================
    # STRUCTURES DE CONTRÔLE (copie-colle tes versions précédentes ici)
    # ===================================================================
    def start(self, children: List, ctx: TransformationContext) -> List[str]:
        lines = []
        for child in children:
            result = self._transform_node(child, ctx)
            if result:
                if isinstance(result, list):
                    lines.extend(result)
                else:
                    lines.append(str(result))
        return lines

    def stmt(self, children: List, ctx: TransformationContext):
        return self._transform_node(children[0], ctx) if children else ""

    def _make_block(self, children: List, ctx: TransformationContext) -> List[str]:
        lines = []
        
        for child in children:
            result = self._transform_node(child, ctx)
            if not result:
                continue
                
            # On s'assure d'avoir une liste de lignes
            child_lines = self._to_lines(result)
            
            for line in child_lines:
                if line.strip():
                    # CRUCIAL : On ajoute l'indentation devant CHAQUE ligne
                    lines.append(ctx.indent() + line)
                    
        return lines


    def _format_block(self, header: str, body_lines: List[str], ctx: TransformationContext) -> List[str]:
        ctx.increase_indent()
        res = [f"{header} {{"]
        for line in body_lines:
            res.append(ctx.indent() + line)
        res.append("}")
        ctx.decrease_indent()
        return res


    def if_stmt(self, children: List, ctx: TransformationContext) -> List[str]:
        cond = self._transform_node(children[0], ctx)
        
        # Extraction propre des sous-blocs
        block_children = [c for c in children[1:] if not (isinstance(c, Tree) and c.data in ('else_if_stmt', 'else_stmt'))]
        else_ifs = [c for c in children[1:] if isinstance(c, Tree) and c.data == 'else_if_stmt']
        else_node = next((c for c in children[1:] if isinstance(c, Tree) and c.data == 'else_stmt'), None)

        # Construction du bloc IF
        body = self._make_block(block_children, ctx)
        lines = self._format_block(f"if ({cond})", body, ctx)

        # Ajout des branches suivantes
        for ei in else_ifs:
            lines.extend(self._transform_node(ei, ctx))
        if else_node:
            lines.extend(self._transform_node(else_node, ctx))
            
        return lines

    def else_if_stmt(self, children: List, ctx: TransformationContext) -> List[str]:
        cond = self._transform_node(children[0], ctx)
        body = self._make_block(children[1:], ctx)
        return self._format_block(f"else if ({cond})", body, ctx)

    def else_stmt(self, children: List, ctx: TransformationContext) -> List[str]:
        body = self._make_block(children, ctx)
        return self._format_block("else", body, ctx)

    def for_range_stmt(self, children: List, ctx: TransformationContext) -> List[str]:
        if len(children) < 4:
            return []
        
        # 1. Extraire les composants fixes
        var = self._transform_node(children[0], ctx)
        start = self._transform_node(children[1], ctx)
        end = self._transform_node(children[2], ctx)
        
        # 2. Gérer le STEP optionnel
        # On regarde si l'enfant à l'index 3 est une expression (step) ou le début du bloc
        step_val = None
        body_start_index = 3
        
        # Si le 4ème enfant n'est pas un Tree de type 'stmt', c'est probablement notre step
        if len(children) > 4 and not (isinstance(children[3], Tree) and children[3].data == 'stmt'):
            step_val = self._transform_node(children[3], ctx)
            body_start_index = 4

        # 3. Collecter le corps
        body = self._make_block(children[body_start_index:], ctx)
        
        # 4. Construire le header GAML
        header = f"loop {var} from: {start} to: {end}"
        if step_val:
            header += f" step: {step_val}"
            
        return self._format_block(header, body, ctx)


    def for_each_stmt(self, children: List, ctx: TransformationContext) -> List[str]:
        if len(children) < 3:
            return []
        
        var = self._transform_node(children[0], ctx)
        collection = self._transform_node(children[1], ctx)
        
        # We collect the body content (stmt*)
        body = self._make_block(children[2:], ctx)
        
        # Use _format_block for consistent GAML loop syntax
        return self._format_block(f"loop {var} over: {collection}", body, ctx)


    def while_stmt(self, children: List, ctx: TransformationContext) -> List[str]:
        if len(children) < 2:
            return []
        
        cond = self._transform_node(children[0], ctx)
        body = self._make_block(children[1:], ctx)
        
        return self._format_block(f"loop while: {cond}", body, ctx)


    def repeat_until_stmt(self, children: List, ctx: TransformationContext) -> List[str]:
        if len(children) < 2:
            return []
        
        # 1. Identifier l'expression (la condition)
        expr_node = next((c for c in children if isinstance(c, Tree) and c.data == 'expr'), None)
        
        # 2. Filtrer le corps : on exclut la condition ET le point-virgule (Token SEMI)
        body_nodes = []
        for c in children:
            if c == expr_node:
                continue
            # On ignore le point-virgule s'il s'agit d'un Token nommé SEMI ou valant ";"
            if hasattr(c, 'type') and c.type == 'SEMI':
                continue
            if hasattr(c, 'value') and c.value == ';':
                continue
            body_nodes.append(c)
        
        # 3. Transformation
        cond = self._transform_node(expr_node, ctx) if expr_node else "false"
        body = self._make_block(body_nodes, ctx)
        
        # 4. Rendu GAML : on utilise "not(cond)" pour simuler "repeat until"
        return self._format_block(f"loop while: not({cond})", body, ctx)


    def switch_stmt(self, children: List, ctx: TransformationContext) -> List[str]:
        """Transforme switch en chaîne if/else if robuste avec indentation correcte."""
        if not children:
            return []

        # 1. Récupérer la variable à tester (ex: soil_type)
        switch_var = self._transform_node(children[0], ctx)
        lines = []
        first_case = True

        for child in children[1:]:
            if not isinstance(child, Tree):
                continue

            # --- CAS : case_stmt ---
            if child.data == 'case_stmt':
                # Extraire la valeur (ex: "sandy")
                val_node = next((c for c in child.children if isinstance(c, Tree) and c.data == 'value'), None)
                value = self._transform_node(val_node, ctx) if val_node else "null"

                # Extraire le corps (tout sauf la valeur et le break)
                body_nodes = [c for c in child.children if not (isinstance(c, Tree) and c.data in ('value', 'break_stmt'))]
                body = self._make_block(body_nodes, ctx)

                # Formater le bloc
                prefix = "if" if first_case else "else if"
                header = f"{prefix} ({switch_var} = {value})"
                
                # Utilisation de l'utilitaire pour un décalage propre
                lines.extend(self._format_block(header, body, ctx))
                first_case = False

            # --- CAS : default_stmt (ou default_list selon votre grammaire) ---
            elif child.data in ('default_stmt', 'default_list'):
                # On ramasse tout le contenu du default
                body = self._make_block(child.children, ctx)
                lines.extend(self._format_block("else", body, ctx))

        return lines

    def break_stmt(self, children: List, ctx: TransformationContext) -> str:
        # Le break est inutile dans une structure if/else if GAML
        return "" 


    def return_stmt(self, children: List, ctx: TransformationContext) -> str:
        if children:
            expr = self._transform_node(children[0], ctx)
            return f"return {expr};"
        return "return;"

    # ===================================================================
    # FONCTIONS ET PROCÉDURES (amélioré)
    # ===================================================================
    def function_decl(self, children: List, ctx: TransformationContext) -> List[str]:
        return self._build_action_declaration(children, ctx, expect_return=True)

    def procedure_decl(self, children: List, ctx: TransformationContext) -> List[str]:
        return self._build_action_declaration(children, ctx, expect_return=False)

    def param_decl(self, children: List, ctx: TransformationContext) -> str:
        """Transforms 'int x' into 'int x' for GAML."""
        if len(children) == 2:
            # Case: TYPE var_name
            var_type = str(children[0])
            var_name = self._transform_node(children[1], ctx)
            return f"{var_type} {var_name}"
        else:
            # Case: var_name (default to unknown/dynamic or float)
            var_name = self._transform_node(children[0], ctx)
            return f"unknown {var_name}"

    def _build_action_declaration(self, children: List, ctx: TransformationContext, expect_return: bool) -> List[str]:
        if not children:
            return ["// empty declaration"]

        # 1. First child is the CNAME (action name)
        name = str(children[0])
        
        params = []
        body_nodes = []
        return_node = None

        # 2. Sort children: separate params from the code body
        for child in children[1:]:
            if isinstance(child, Tree):
                if child.data == 'param_decl':
                    params.append(self._transform_node(child, ctx))
                elif child.data == 'return_stmt':
                    return_node = child
                else:
                    body_nodes.append(child)
            else:
                # Handle potential loose tokens
                body_nodes.append(child)

        # 3. Build Body
        body = self._make_block(body_nodes, ctx)
        if return_node:
            body.append(self._transform_node(return_node, ctx))
        elif expect_return:
            body.append("// WARNING: return non trouvé dans une function, ajout d'un return par défaut")

        # 4. Final Formatting
        param_str = ", ".join(params)
        header = f"action {name} ({param_str})"
        
        return self._format_block(header, body, ctx)


    # ===================================================================
    # E/S
    # ===================================================================
    def io_stmt(self, children: List, ctx: TransformationContext) -> str:
        if not children:
            return "// empty io_stmt"

        if isinstance(children[0], Token) and children[0].value.lower() == "read":
            expr = self._transform_node(children[1], ctx) if len(children) > 1 else ""
            return f"// read {expr} - not implemented in GAML"
        else:
            # print ou write
            expr = self._transform_node(children[0] if isinstance(children[0], Tree) else children[1] if len(children) > 1 else "", ctx)
            return f"write {expr};" if expr else "// unknown io statement"

    # ===================================================================
    # UTILITAIRES
    # ===================================================================
    def value(self, children: List, ctx: TransformationContext):
        if children:
            return self._transform_node(children[0], ctx)
        return ""

    def number(self, children: List, ctx: TransformationContext) -> str:
        if children and isinstance(children[0], Token):
            return children[0].value
        return "0"


# Fonction utilitaire
def transform_to_gaml(parse_result: ParseResult,
                      variable_collection: CollectionResult,
                      logger: Optional[logging.Logger] = None) -> str:
    transformer = GamlASTTransformer(logger)
    return transformer.transform(parse_result, variable_collection)