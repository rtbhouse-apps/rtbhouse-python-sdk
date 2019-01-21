#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`"
cd ..

if ! [ -x "$(command -v twine)" ]; then
  echo "Missing twine binary, run \"pip install --user --upgrade twine\"" >&2
  exit 1
fi


rm -rf dist
./venv/bin/python setup.py sdist
twine upload dist/*