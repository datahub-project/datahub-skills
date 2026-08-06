#!/usr/bin/env bash
# Read-only: what does a failing table endanger downstream? Traverses column-level
# lineage across the ML boundary and prints the models and live deployments at risk.
# Writes nothing (--dry-run). Usage: check_blast_radius.sh <table-name-or-urn>
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <table-name-or-urn>   e.g. $0 loans_raw" >&2
  exit 2
fi

janus scan --table "$1" --no-llm --dry-run
