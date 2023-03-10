#!/usr/bin/env bash

set -ex

# Rewrite names to install dstate
if [ "$(uname)" == "Darwin" ]; then
    sed -i '' 's/name = "dstate"/name = "dstate-test-package"/' pyproject.toml
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    sed -i 's/name = "dstate"/name = "dstate-test-package"/' pyproject.toml
fi
# Thx: https://stackoverflow.com/a/17072017

# Install dstate from the latest build library
poetry add dist/`ls dist/ | sort -r | head -n 1`
