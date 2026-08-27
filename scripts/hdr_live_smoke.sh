#!/usr/bin/env bash
# Deploy-host P1 smoke. Requires hermes on PATH. Does not commit secrets.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:-research-bot-hdr}"
hermes profile install "$ROOT/agents/research-bot" --name "$NAME" --yes --force
hermes -p "$NAME" tools list
hermes -p "$NAME" skills list
hermes -p "$NAME" plugins list
