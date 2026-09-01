#!/usr/bin/env bash
# Write back: raise the incident, tag the at-risk models, record risk flags and the
# trust score, leave a freshness guarding assertion, and publish the Model Impact
# Report. Idempotent: a second run of an unchanged graph writes nothing. Pass
# --review to janus for an approval prompt before any write lands.
# Usage: guard.sh <table-name-or-urn>
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <table-name-or-urn>   e.g. $0 loans_raw" >&2
  exit 2
fi

janus scan --table "$1" --review
