#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`/.."


poetry run python -m pytest --junitxml=./results/results.xml --color=no --cov-report=term-missing --cov=rtbhouse_sdk/ tests/
