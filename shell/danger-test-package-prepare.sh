#!/usr/bin/env bash

set -ex

# Cleanup previous call
rm -rf ../dstate-test-package

# Copy current ./ to the new package
cp -rf ./ ../dstate-test-package

# Cwd
cd ../dstate-test-package
