#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`/.."


uv run python -m pytest --color=no --cov-report=term-missing --cov=rtbhouse_sdk/ tests/
