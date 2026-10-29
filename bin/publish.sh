#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`/.."

if [[ -z $PYPI_TOKEN ]]; then
  echo -e "Error: please provide PYPI_TOKEN env var"
  exit 1
fi

uv build
uv publish --token "$PYPI_TOKEN"
