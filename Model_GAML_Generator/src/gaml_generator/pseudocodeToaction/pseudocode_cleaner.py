# Cleaner → Lark Parser → VariableCollector → GamlASTTransformer → GamlEmitter
import re
import html
import logging
from typing import List, Tuple, Optional, Dict, Callable
from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum

# Structure pour représenter un token
Token = namedtuple('Token', ['type', 'value', 'start', 'end'])

class TokenType(Enum):
    STRING = "STRING"
    COMMENT_BLOCK = "COMMENT_BLOCK"
    COMMENT_LINE = "COMMENT_LINE"
    KEYWORD = "KEYWORD"
    OPERATOR = "OPERATOR"
    NUMBER = "NUMBER"
    BOOL = "BOOL"
    IDENTIFIER = "IDENTIFIER"
    PUNCTUATION = "PUNCTUATION"
    WHITESPACE = "WHITESPACE"
    NEWLINE = "NEWLINE"
    PROTECTED = "PROTECTED"
    UNKNOWN = "UNKNOWN"

@dataclass
class Annotation:
    """Représente une annotation trouvée dans le code"""
    value: str
    position: int
    line: int
    type: str  # 'resource' ou 'property'
    id: str    # l'ID numérique

@dataclass
class CleanedCode:
    """Résultat du nettoyage avec métadonnées"""
    code: str = ""
    warnings: List[str] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)
    statistics: Dict[str, int] = field(default_factory=dict)
    original_length: int = 0
    cleaned_length: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'code': self.code,
            'warnings': self.warnings,
            'annotations': [vars(a) for a in self.annotations],
            'statistics': self.statistics,
            'original_length': self.original_length,
            'cleaned_length': self.cleaned_length
        }

class AnnotationNormalizer:
    """Normalise les annotations de manière cohérente"""

    @staticmethod
    def normalize(comment: str) -> Tuple[str, Optional[Annotation]]:
        resource_match = re.search(r'resource_(\d+)', comment)
        if resource_match:
            resource_id = resource_match.group(1)
            normalized = f"/* resource_{resource_id} */"  # garder format bloc
            annotation = Annotation(
                value=normalized,
                position=0,
                line=0,
                type='resource',
                id=resource_id
            )
            return normalized, annotation

        property_match = re.search(r'property_(\d+)', comment)
        if property_match:
            property_id = property_match.group(1)
            normalized = f"/*property_{property_id}*/"  # garder format bloc
            annotation = Annotation(
                value=normalized,
                position=0,
                line=0,
                type='property',
                id=property_id
            )
            return normalized, annotation

        return comment, None


class PseudoCodeCleaner:
    """
    Cleaner robuste pour pseudo-code DSL.
    - Décodage HTML
    - Protection des chaînes et commentaires
    - Normalisation des mots-clés et opérateurs
    - Ajustements structurels minimaux
    - Validation avec warnings uniquement
    - Extensible via hooks
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.pre_hooks: List[Callable[[str], str]] = []
        self.post_hooks: List[Callable[[str], str]] = []
        self.annotation_normalizer = AnnotationNormalizer()
        
        # Patterns pour le lexer (ordre important)
        self.token_patterns = [
            (TokenType.STRING, r'"(?:\\.|[^"\\])*"'),  # chaînes entre guillemets
            (TokenType.COMMENT_BLOCK, r'/\*.*?\*/', re.DOTALL),  # commentaires multi-lignes
            (TokenType.COMMENT_LINE, r'//[^\n]*'),     # commentaires ligne
            (TokenType.KEYWORD, r'\b(if|else|for|each|in|while|repeat|until|switch|case|default|break|return|procedure|function|read|print|and|or|not|true|false)\b', re.IGNORECASE),
            (TokenType.OPERATOR, r'(\+=|-=|\*=|/=|==|!=|>=|<=|&&|\|\||[+\-*/^<>!&|]=?)'),  # opérateurs
            (TokenType.NUMBER, r'\b\d+(?:\.\d+)?\b'),
            (TokenType.BOOL, r'\btrue\b|\bfalse\b', re.IGNORECASE),
            (TokenType.IDENTIFIER, r'[a-zA-Z_][a-zA-Z0-9_]*'),
            (TokenType.PUNCTUATION, r'[(){}\[\],;:]'),
            (TokenType.WHITESPACE, r'\s+'),
            (TokenType.NEWLINE, r'\n'),
            (TokenType.UNKNOWN, r'.'),  # tout autre caractère
        ]
        
        # Compilation des patterns
        self.compiled_patterns = []
        for pattern in self.token_patterns:
            if len(pattern) == 3:
                ttype, regex, flags = pattern
            else:
                ttype, regex = pattern
                flags = 0
            self.compiled_patterns.append((ttype, re.compile(regex, flags)))
        
        # Mapping de normalisation
        self.normalize_map = {
            # Mots-clés (minuscules)
            'AND': 'and',
            'OR': 'or',
            'NOT': 'not',
            'TRUE': 'true',
            'FALSE': 'false',
            # Opérateurs
            '&&': 'and',
            '||': 'or',
        }

    def add_pre_hook(self, func: Callable[[str], str]) -> None:
        """Ajoute un hook exécuté avant le nettoyage principal"""
        self.pre_hooks.append(func)

    def add_post_hook(self, func: Callable[[str], str]) -> None:
        """Ajoute un hook exécuté après le nettoyage principal"""
        self.post_hooks.append(func)

    def clean(self, raw_code: Optional[str]) -> CleanedCode:
        """
        Nettoie le code pseudo et retourne un objet CleanedCode avec métadonnées
        """
        result = CleanedCode()
        
        if not raw_code or not raw_code.strip():
            result.warnings.append("Code vide reçu")
            return result
        
        result.original_length = len(raw_code)
        
        try:
            # Hooks pré-traitement
            code = raw_code
            for hook in self.pre_hooks:
                code = hook(code)
            
            # 1. Prétraitement global
            code = self._preprocess(code)
            
            # 2. Tokenisation
            tokens, unknown_count = self._tokenize(code)
            
            # 3. Protection des chaînes et commentaires
            protected_tokens, protected_map, annotations = self._protect_tokens(tokens)
            result.annotations = annotations
            
            # 4. Normalisation des tokens
            normalized_tokens = self._normalize_tokens(protected_tokens)
            
            # 5. Restauration
            restored_code = self._restore_tokens(normalized_tokens, protected_map)
            
            # 6. Ajustements structurels minimaux
            adjusted_code = self._adjust_structure(restored_code)
            
            # 7. Validation (avec warnings seulement)
            validation_warnings = self._validate(adjusted_code)
            result.warnings.extend(validation_warnings)
            
            # Statistiques
            result.statistics = {
                'tokens_total': len(tokens),
                'tokens_unknown': unknown_count,
                'annotations_found': len(annotations),
                'lines_processed': len(adjusted_code.split('\n'))
            }
            
            # Hooks post-traitement
            for hook in self.post_hooks:
                adjusted_code = hook(adjusted_code)
            
            result.code = adjusted_code.strip()
            result.cleaned_length = len(result.code)
            
            # Warning si des caractères inconnus ont été trouvés
            if unknown_count > 0:
                result.warnings.append(f"{unknown_count} caractère(s) non reconnu(s) ont été ignorés")
            
        except Exception as e:
            error_msg = f"Erreur lors du nettoyage: {str(e)}"
            self.logger.error(error_msg)
            result.warnings.append(error_msg)
            # En cas d'erreur, retourner le code original nettoyé minimalement
            result.code = self._minimal_clean(raw_code)
        
        return result

    # ------------------------------------------------------------------
    # Étape 1 : Prétraitement
    # ------------------------------------------------------------------
    def _preprocess(self, code: str) -> str:
        """Décodage HTML, normalisation des fins de ligne, etc."""
        # Décoder les entités HTML
        code = html.unescape(code)
        # Remplacer \r\n par \n
        code = code.replace('\r\n', '\n').replace('\r', '\n')
        # Supprimer les caractères de contrôle sauf \n et \t
        code = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', code)
        return code

    # ------------------------------------------------------------------
    # Étape 2 : Tokenisation
    # ------------------------------------------------------------------
    def _tokenize(self, code: str) -> Tuple[List[Token], int]:
        """Tokenise le code et retourne (tokens, nombre_d_inconnus)"""
        tokens = []
        unknown_count = 0
        pos = 0
        
        while pos < len(code):
            match = None
            for ttype, pattern in self.compiled_patterns:
                match = pattern.match(code, pos)
                if match:
                    value = match.group(0)
                    tokens.append(Token(ttype, value, pos, match.end()))
                    pos = match.end()
                    break
                    
            if not match:
                unknown_count += 1
                char = code[pos]
                self.logger.debug(f"Caractère non reconnu à la position {pos}: '{char}' (0x{ord(char):02x})")
                tokens.append(Token(TokenType.UNKNOWN, char, pos, pos+1))
                pos += 1
        
        return tokens, unknown_count

    # ------------------------------------------------------------------
    # Étape 3 : Protection
    # ------------------------------------------------------------------
    def _protect_tokens(self, tokens: List[Token]) -> Tuple[List[Token], Dict[str, str], List[Annotation]]:
        """
        Protège les chaînes et commentaires avec des marqueurs.
        Retourne (tokens_protégés, map_marqueurs, liste_annotations)
        """
        protected_tokens = []
        protected_map = {}
        annotations = []
        counter = 0
        current_line = 1
        
        for token in tokens:
            if token.type == TokenType.NEWLINE:
                current_line += 1
                protected_tokens.append(token)
                continue
                
            if token.type in (TokenType.STRING, TokenType.COMMENT_BLOCK, TokenType.COMMENT_LINE):
                value = token.value
                
                # Normaliser les annotations si c'est un commentaire bloc
                if token.type == TokenType.COMMENT_BLOCK:
                    normalized_value, annotation = self.annotation_normalizer.normalize(value)
                    if annotation:
                        annotation.position = token.start
                        annotation.line = current_line
                        annotations.append(annotation)
                        value = normalized_value
                
                marker = f"__PROTECTED_{counter}__"
                protected_map[marker] = value
                protected_tokens.append(Token(TokenType.PROTECTED, marker, token.start, token.end))
                counter += 1
            else:
                protected_tokens.append(token)
        
        return protected_tokens, protected_map, annotations

    # ------------------------------------------------------------------
    # Étape 4 : Normalisation
    # ------------------------------------------------------------------
    def _normalize_tokens(self, tokens: List[Token]) -> List[Token]:
        """
        Applique les transformations sur les tokens de code (hors PROTECTED)
        """
        normalized = []
        
        for token in tokens:
            if token.type == TokenType.PROTECTED:
                normalized.append(token)
                continue
                
            if token.type == TokenType.KEYWORD:
                # Mettre en minuscules et appliquer le mapping
                new_value = token.value.lower()
                new_value = self.normalize_map.get(new_value.upper(), new_value)
                normalized.append(Token(token.type, new_value, token.start, token.end))
                
            elif token.type == TokenType.OPERATOR:
                op = token.value
                if op == '&&':
                    op = 'and'
                elif op == '||':
                    op = 'or'
                elif op == '!':
                    op = 'not'
                normalized.append(Token(token.type, op, token.start, token.end))
                
            elif token.type == TokenType.BOOL:
                # Mettre en minuscules
                normalized.append(Token(token.type, token.value.lower(), token.start, token.end))
                
            else:
                normalized.append(token)
        
        return normalized

    # ------------------------------------------------------------------
    # Étape 5 : Restauration
    # ------------------------------------------------------------------
    def _restore_tokens(self, tokens: List[Token], protected_map: Dict[str, str]) -> str:
        """Reconstruit le code à partir des tokens"""
        parts = []
        
        for token in tokens:
            if token.type == TokenType.PROTECTED:
                parts.append(protected_map[token.value])
            else:
                parts.append(token.value)
        
        return ''.join(parts)

    # ------------------------------------------------------------------
    # Étape 6 : Ajustements structurels minimaux
    # ------------------------------------------------------------------
    def _adjust_structure(self, code: str) -> str:
        """
        Ajustements minimaux :
        - Normalise l'indentation (tabs -> 4 espaces)
        - Supprime les espaces en fin de ligne
        - Pas d'ajout automatique de points-virgules
        """
        lines = code.split('\n')
        new_lines = []
        
        for line in lines:
            # Remplacer les tabs par 4 espaces
            line = line.replace('\t', '    ')
            # Supprimer les espaces en fin de ligne
            line = line.rstrip()
            new_lines.append(line)
        
        return '\n'.join(new_lines)

    # ------------------------------------------------------------------
    # Étape 7 : Validation (warnings uniquement)
    # ------------------------------------------------------------------
    def _validate(self, code: str) -> List[str]:
        """
        Valide le code et retourne une liste de warnings.
        Ne lève jamais d'exception.
        """
        warnings = []
        
        lines = code.split('\n')
        brace_level = 0
        paren_level = 0
        bracket_level = 0
        in_multiline_comment = False
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            
            # Gestion des commentaires blocs
            if '/*' in line and '*/' not in line:
                in_multiline_comment = True
            if '*/' in line:
                in_multiline_comment = False
                continue
            
            # Ne pas valider les lignes de commentaire
            if stripped.startswith('//') or in_multiline_comment:
                continue
            
            # Compter les délimiteurs
            for char in line:
                if char == '{':
                    brace_level += 1
                elif char == '}':
                    brace_level -= 1
                    if brace_level < 0:
                        warnings.append(f"Ligne {i}: '}}' sans ouverture")
                        brace_level = 0  # Réinitialiser pour éviter les warnings en cascade
                elif char == '(':
                    paren_level += 1
                elif char == ')':
                    paren_level -= 1
                    if paren_level < 0:
                        warnings.append(f"Ligne {i}: ')' sans ouverture")
                        paren_level = 0
                elif char == '[':
                    bracket_level += 1
                elif char == ']':
                    bracket_level -= 1
                    if bracket_level < 0:
                        warnings.append(f"Ligne {i}: ']' sans ouverture")
                        bracket_level = 0
            
            # Vérifier les mots-clés then (interdit)
            if re.search(r'\bthen\b', stripped, re.IGNORECASE):
                warnings.append(f"Ligne {i}: 'then' est un mot-clé interdit")
        
        # Vérifications globales
        if brace_level > 0:
            warnings.append(f"Accolades non fermées (niveau {brace_level})")
        if paren_level > 0:
            warnings.append(f"Parenthèses non fermées (niveau {paren_level})")
        if bracket_level > 0:
            warnings.append(f"Crochets non fermés (niveau {bracket_level})")
        
        return warnings

    # ------------------------------------------------------------------
    # Méthodes utilitaires
    # ------------------------------------------------------------------
    def _minimal_clean(self, raw_code: str) -> str:
        """Nettoyage minimal de secours en cas d'erreur"""
        # Simplement enlever les caractères de contrôle et normaliser les fins de ligne
        code = html.unescape(raw_code)
        code = code.replace('\r\n', '\n').replace('\r', '\n')
        code = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', code)
        return code.strip()


# ------------------------------------------------------------------
# Fonctions utilitaires pour une utilisation facile
# ------------------------------------------------------------------
def clean_pseudo_code(code: str, logger: Optional[logging.Logger] = None) -> str:
    """
    Fonction simplifiée pour nettoyer du pseudo-code.
    Retourne le code nettoyé sous forme de string.
    """
    cleaner = PseudoCodeCleaner(logger)
    result = cleaner.clean(code)
    return result.code

def clean_pseudo_code_with_metadata(code: str, logger: Optional[logging.Logger] = None) -> CleanedCode:
    """
    Fonction simplifiée pour nettoyer du pseudo-code avec métadonnées.
    Retourne un objet CleanedCode contenant le code et les métadonnées.
    """
    cleaner = PseudoCodeCleaner(logger)
    return cleaner.clean(code)