#!/usr/bin/env bash
# Seed the demo ML supply chain the datapacks lack, then plant a stale-upstream
# scenario so the checks have something to find. Idempotent: re-running re-upserts.
set -euo pipefail

janus-seed
janus-scenario --lag-hours 30
