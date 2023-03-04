#!/usr/bin/env bash

set -x

docker compose -f full_tests/compose/docker-compose-mongo.yaml up -d
