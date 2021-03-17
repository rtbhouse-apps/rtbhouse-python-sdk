#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`/.."

if [[ -z $PYPI_TOKEN ]]; then
  echo -e "Error: please provide PYPI_TOKEN env var"
  exit 1
fi

poetry publish --build --no-interaction -u __token__ -p $PYPI_TOKEN
