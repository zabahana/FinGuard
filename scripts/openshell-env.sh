#!/bin/sh
# Source from repository root. All operator state stays outside sandbox build contexts.
export XDG_CONFIG_HOME="$PWD/.local/openshell/config"
export XDG_STATE_HOME="$PWD/.local/openshell/state"
export OPENSHELL_LOCAL_TLS_DIR="$PWD/.local/openshell/tls-desktop"
export PATH="$PWD/.local/openshell:$PATH"
