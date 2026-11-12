class DocumentationError(Exception):
    """Base pour toutes les erreurs de documentation"""

class SectionGenerationError(DocumentationError):
    def __init__(self, section_name: str, original_error: Exception):
        super().__init__(f"Erreur dans la section {section_name}: {str(original_error)}")
        self.original_error = original_error

class InvalidModelError(DocumentationError):
    """Données du modèle invalides"""