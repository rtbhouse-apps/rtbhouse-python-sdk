#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`/.."

exit_code=0

if poetry show | cut -f 1 -d ' ' | grep \^black\$ > /dev/null; then
  echo -e "\nRunning black..."
  poetry run black --check . || exit_code=1
fi

if poetry show | cut -f 1 -d ' ' | grep \^isort\$ > /dev/null; then
  echo -e "\nRunning isort..."
  poetry run isort -c -q . || exit_code=1
fi

if poetry show | cut -f 1 -d ' ' | grep \^flake8\$ > /dev/null; then
  echo -e "\nRunning flake8..."
  poetry run flake8 || exit_code=1
fi

exit $exit_code
