#!/bin/bash

# Script pour corriger l'encodage des fichiers JSON

echo "Correction de l'encodage des fichiers JSON..."

# Corriger config.json
if [ -f "config.json" ]; then
    echo "Correction de config.json..."
    iconv -f ISO-8859-1 -t UTF-8 config.json > config_fixed.json
    mv config_fixed.json config.json
    echo "✓ config.json corrigé"
fi

# Corriger les autres fichiers JSON dans input/
for json_file in input/*.json; do
    if [ -f "$json_file" ]; then
        echo "Correction de $json_file..."
        iconv -f ISO-8859-1 -t UTF-8 "$json_file" > "${json_file}.fixed"
        mv "${json_file}.fixed" "$json_file"
        echo "✓ $json_file corrigé"
    fi
done

echo "Correction terminée !"