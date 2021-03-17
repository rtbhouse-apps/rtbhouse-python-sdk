#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`/.."


poetry run python -m pytest --cov=rtbhouse_sdk/ tests/
