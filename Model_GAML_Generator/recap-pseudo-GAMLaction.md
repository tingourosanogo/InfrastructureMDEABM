# Pipeline de Transformation Pseudo-code → GAML

## Vue d'ensemble du pipeline

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ PIPELINE DE TRANSFORMATION │
├─────────────────────────────────────────────────────────────────────────────┤
│ │
│ ┌──────────┐ ┌──────────┐ ┌─────────────────┐ ┌───────────────┐ │
│ │ Pseudo │ │ Cleaner │ │ Lark Parser │ │ Variable │ │
│ │ Code │───▶│ │───▶│ │───▶│ Collector │ │
│ │ (String) │ │ │ │ │ │ │ │
│ └──────────┘ └──────────┘ └─────────────────┘ └───────────────┘ │
│ │ │ │ │
│ ▼ ▼ ▼ │
│ ┌──────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ CleanedCode │ │ ParseResult │ │ CollectionResult│ │
│ │ • code │ │ • tree │ │ • variables │ │
│ │ • warnings │ │ • warnings │ │ • functions │ │
│ │ • annotations│ │ • metadata │ │ • annotations │ │
│ │ • statistics │ │ • parse_time │ │ • global_vars │ │
│ └──────────────┘ └─────────────────┘ └─────────────────┘ │
│ │ │ │
│ ▼ ▼ │
│ ┌─────────────────────────────────────────┐ │
│ │ GamlASTTransformer │ │
│ │ │ │
│ │ Transforme l'AST en code GAML │ │
│ │ avec gestion des opérateurs, │ │
│ │ structures de contrôle et │ │
│ │ fonctions/procédures │ │
│ └─────────────────────────────────────────┘ │
│ │ │
│ ▼ │
│ ┌─────────────────────────────────────────┐ │
│ │ GamlEmitter │ │
│ │ │ │
│ │ Génère le code GAML final avec │ │
│ │ action, reflex, commentaires et │ │
│ │ métadonnées │ │
│ └─────────────────────────────────────────┘ │
│ │ │
│ ▼ │
│ ┌──────────────┐ │
│ │ Code GAML │ │
│ │ (String) │ │
│ └──────────────┘ │
│ │
└─────────────────────────────────────────────────────────────────────────────┘
```


## Diagramme de flux des données 

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FLUX DES DONNÉES                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  PseudoCode (str)                                                                   │
│       │                                                                             │
│       ▼                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │ Cleaner                                                                      │   │
│  │ • Décodage HTML                                                              │   │
│  │ • Protection chaînes/commentaires                                            │   │
│  │ • Normalisation mots-clés                                                    │   │
│  │ • Extraction annotations                                                     │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                             │
│       ▼                                                                             │
│  CleanedCode { code, warnings, annotations, statistics }                           │
│       │                                                                             │
│       ▼                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │ Lark Parser                                                                  │   │
│  │ • Parsing avec grammaire Lark                                                │   │
│  │ • Génération AST                                                             │   │
│  │ • Validation post-parsing                                                    │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                             │
│       ▼                                                                             │
│  ParseResult { tree, success, warnings, errors, metadata }                         │
│       │                                                                             │
│       ▼                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │ VariableCollector                                                            │   │
│  │ • Parcours AST                                                               │   │
│  │ • Gestion scopes (pile)                                                      │   │
│  │ • Association annotations ↔ variables                                        │   │
│  │ • Détection fonctions/paramètres                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                             │
│       ▼                                                                             │
│  CollectionResult { variables, functions, global_variables, warnings }             │
│       │                                                                             │
│       ▼                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │ GamlASTTransformer                                                           │   │
│  │ • Mapping opérateurs                                                         │   │
│  │ • Transformation structures contrôle                                         │   │
│  │ • Conversion fonctions → actions                                             │   │
│  │ • Conservation annotations en commentaires                                   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                             │
│       ▼                                                                             │
│  GamlCode (str)                                                                    │
│       │                                                                             │
│       ▼                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │ GamlEmitter                                                                  │   │
│  │ • Construction action GAML                                                   │   │
│  │ • Génération reflex optionnel                                                │   │
│  │ • Ajout en-tête et commentaires                                              │   │
│  │ • Nettoyage final                                                            │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                             │
│       ▼                                                                             │
│  Code GAML (str)                                                                    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```
