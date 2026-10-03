#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
. scripts/openshell-env.sh
exec openshell-gateway --config .local/openshell/gateway.toml
