#!/usr/bin/env python3
"""
Module d'aide pour la ligne de commande
Affiche des exemples d'utilisation et de l'aide contextuelle
"""

def show_usage_examples():
    """Affiche des exemples d'utilisation"""
    examples = [
        "# Génération simple",
        "python main.py",
        "",
        "# Avec configuration spécifique", 
        "python main.py --config mon_config.json --output ma_documentation.md",
        "",
        "# Génération partielle (sections spécifiques)",
        "python main.py --sections cover,structure --output partial_docs.md",
        "",
        "# Mode verbose pour le débogage",
        "python main.py --verbose --debug",
        "",
        "# Générer seulement Markdown",
        "python main.py --config config.json",
        "",
        "# Générer Markdown + HTML",
        "python main.py --export html",
        "",
        "# Générer Markdown + HTML + PDF", 
        "python main.py --export html pdf",
        "",
        "# Avec CSS personnalisé",
        "python main.py --export html pdf --css assets/custom.css",
        "",
        "# Spécifier le dossier d'export",
        "python main.py --export html pdf --export-dir docs/export",
        "",
        "# Générer seulement PDF",
        "python main.py --export pdf",
        "",
        "# Forcer la régénération",
        "python main.py --force",
        "",
        "# Valider les fichiers d'entrée",
        "python main.py --validate",
        "",
        "# Chemin XMI personnalisé",
        "python main.py --xmi-path mon_modele.xmi"
    ]
    
    print("Exemples d'utilisation:\n")
    for example in examples:
        if example.startswith("#"):
            print(f"\n\033[1;36m{example}\033[0m")
        else:
            print(f"  \033[1;32m{example}\033[0m")

def show_section_help():
    """Affiche l'aide sur les sections disponibles"""
    sections = {
        'cover': 'Page de garde avec métadonnées',
        'structure': 'Structure du modèle conceptuel (XMI)',
        'manual': 'Mode d\'emploi et instructions',
        'indicators': 'Indicateurs et métriques',
        'init': 'Données d\'initialisation'
    }
    
    print("Sections disponibles:\n")
    for section, description in sections.items():
        print(f"  \033[1;32m{section:<12}\033[0m - {description}")

if __name__ == "__main__":
    show_usage_examples()
    print("\n" + "="*60)
    show_section_help()