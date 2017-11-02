#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`"
cd ../tests


../virtualenv/bin/python -m unittest test_reports_api.py