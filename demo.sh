#!/bin/sh
# Demo: one stable fact, one invented premise. Needs SE_ENDPOINT (defaults to LM Studio local).
set -e
echo "=== Stable fact (expect: STABLE, low entropy) ==="
python3 semantic_entropy.py --question "What is the capital of Australia?"
echo ""
echo "=== Invented premise (expect: scatter / refusal-worthy) ==="
python3 semantic_entropy.py --question "What did the 1962 Brookfield Accord establish?"
