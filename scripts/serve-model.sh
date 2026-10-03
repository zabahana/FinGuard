#!/bin/sh
# Run the project-local Ollama installation with cloud inference disabled.
set -eu
cd "$(dirname "$0")/.."
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_NO_CLOUD=1
export OLLAMA_MODELS="$PWD/.local/models"
exec .local/Ollama.app/Contents/Resources/ollama serve
