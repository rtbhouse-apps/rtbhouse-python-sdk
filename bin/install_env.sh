#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`"
cd ..

rm -rf ./virtualenv
python3 -m venv ./virtualenv
./virtualenv/bin/pip install -U pip setuptools wheel
./virtualenv/bin/pip install -e .