# version 2 pour validations détection de ; manquant sur certaines lignes

import re
import html
import logging
from typing import Optional

class PseudoCodeCleaner:
    """
    Préprocesseur robuste pour le pseudoCode avant parsing Lark.
    - Décodage HTML
    - Protection stricte des annotations /* resource_xxx */ et /* property_xxx */
    - Suppression des autres commentaires /* ... */
    - Normalisation minimale
    - Validation stricte du standard + détection des ; manquants sur instructions
    """

    def __init__(self, logger: Optional[logging.Logger] = None, strict: bool = True):
        self.logger = logger or logging.getLogger(__name__)
        self.strict = strict  # True = lève exception sur erreurs critiques

    def clean(self, raw_code: Optional[str]) -> str:
        if not raw_code or not raw_code.strip():
            return ""

        # 1. Décodage HTML
        code = html.unescape(raw_code)

        # 2. Protéger les annotations
        annotations = {}
        def protect_annotation(m):
            key = f"__ANNOT_{len(annotations):04d}__"
            annotations[key] = m.group(0)
            return key

        code = re.sub(
            r'/\*\s*(resource_\d+|property_\d+)\s*\*/',
            protect_annotation,
            code,
            flags=re.IGNORECASE
        )

        # 3. Supprimer les autres commentaires /* ... */
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

        # 4. Restaurer les annotations
        for key, value in annotations.items():
            code = code.replace(key, value)

        # 5. Normalisation légère
        lines = []
        for line in code.splitlines():
            leading_ws = re.match(r'^[ \t]*', line).group(0)
            content = line[len(leading_ws):].rstrip()  # rstrip pour éviter espaces en fin

            if content:
                # Normaliser espaces internes
                content = re.sub(r'[ \t]+', ' ', content)
                lines.append(leading_ws + content)
            else:
                lines.append(leading_ws)

        cleaned = '\n'.join(lines).strip()

        # 6. Validation complète (standard + ; manquants)
        self._validate_standard_and_semicolons(cleaned)

        self.logger.debug("PseudoCode nettoyé et validé avec succès.")
        return cleaned

    def _validate_standard_and_semicolons(self, code: str) -> None:
        """
        Validation du standard + détection des ; manquants sur les instructions.
        """
        errors = []
        warnings = []

        lines = code.splitlines()
        brace_level = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue

            # --- Validations standard déjà existantes ---
            if re.search(r'\bthen\b', stripped, re.IGNORECASE):
                errors.append(f"Ligne {i}: Mot-clé 'then' interdit")

            if re.match(r'^\s*if\s+(?!.*\()', stripped, re.IGNORECASE):
                errors.append(f"Ligne {i}: 'if' sans parenthèses ( )")

            if re.match(r'^\s*else\s+(?!{)', stripped, re.IGNORECASE):
                warnings.append(f"Ligne {i}: 'else' sans {{}} immédiatement après ?")

            # Comptage accolades
            for char in line:
                if char == '{':
                    brace_level += 1
                elif char == '}':
                    brace_level -= 1
                    if brace_level < 0:
                        errors.append(f"Ligne {i}: '}}' sans ouverture correspondante")

            # --- NOUVELLE : Détection des ; manquants ---
            # On ignore les lignes de contrôle / commentaires / annotations seules
            if (
                stripped.startswith('//') or
                stripped.startswith('if ') or
                stripped.startswith('else') or
                stripped.startswith('for each') or
                stripped.startswith('while ') or
                stripped.startswith('switch ') or
                stripped.startswith('case ') or
                stripped.startswith('default:') or
                stripped == '{' or
                stripped == '}' or
                stripped.endswith('{') or
                stripped.endswith('}') or
                stripped.startswith('/*')  # annotation seule
            ):
                continue

            # Si la ligne ne finit pas par ; et n'est pas un bloc, c'est suspect
            if not stripped.endswith(';'):
                # Exceptions tolérées : lignes vides ou purement indentées
                if stripped and not re.match(r'^\s*$', stripped):
                    msg = f"Ligne {i}: Instruction probable sans ';' en fin (ex. affectation ou appel ?)"
                    if self.strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)

        if brace_level > 0:
            errors.append(f"{brace_level} accolade(s) ouvrante(s) '{{' non fermée(s)")

        # Erreurs critiques
        if errors:
            msg = "Erreurs critiques dans le pseudoCode :\n" + "\n".join(errors)
            if self.strict:
                raise ValueError(msg)
            else:
                self.logger.error(msg)

        # Warnings non bloquants
        if warnings:
            self.logger.warning("Avertissements (non bloquants) :\n" + "\n".join(warnings))