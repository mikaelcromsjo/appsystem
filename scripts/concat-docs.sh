#!/bin/bash

# Concatenate all key documentation into full-doc.md
# Usage: bash scripts/concat-docs.sh

output_file="full-doc.md"

cat docs/PATTERNS.md docs/STRUCTURE.md docs/MODELS.md docs/IMPORTS.md docs/DOCS.md > "$output_file"

echo "✓ Created $output_file ($(wc -l < "$output_file") lines)"
