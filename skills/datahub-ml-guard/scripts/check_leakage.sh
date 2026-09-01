#!/usr/bin/env bash
# Read-only: audit a model for target leakage and input schema drift. Resolves the
# model to its features to their source columns and checks whether any feature
# derives from the model's own label, or whether an input's schema drifted from
# training. Writes nothing (--dry-run). Usage: check_leakage.sh <model-name-or-urn>
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <model-name-or-urn>   e.g. $0 credit_risk_v3" >&2
  exit 2
fi

janus scan --model "$1" --no-llm --dry-run
