#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`"
cd ..

rm -rf ./venv
python3 -m venv venv
export PATH="./venv/bin:$PATH"

pip install -U pip setuptools wheel
pip install -e .[dev]
pip list --outdated