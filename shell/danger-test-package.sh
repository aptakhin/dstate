#!/usr/bin/env bash

set -ex

poetry build

# Cleanup previous call
rm -rf ../dstate-test-package

# Copy current ./ to the new package
cp -rf ./ ../dstate-test-package

# Cwd
cd ../dstate-test-package

# Rewrite names to install dstate: Mac sed version
sed -i '' 's/name = "dstate"/name = "dstate-test-package"/' pyproject.toml

# Install dstate from the latest build library
poetry add dist/`ls dist/ | sort -r | head -n 1`

export PYTHONPATH=.
./shell/pytest-smoke.sh
./shell/pytest-full.sh
