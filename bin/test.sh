#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`"
cd ..


./venv/bin/py.test tests/