#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`"
cd ..


./venv/bin/python tests/test_reports_api.py