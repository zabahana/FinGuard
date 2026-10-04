#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
. scripts/openshell-env.sh
exec .venv/bin/python scripts/run-attack-lab.py
