#!/usr/bin/env bash

set -x

docker compose -f full_tests/compose/docker-compose-mongo.yaml stop
docker compose -f full_tests/compose/docker-compose-mongo.yaml rm -f
