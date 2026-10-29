#!/usr/bin/env bash

set -e
set -o pipefail

cd "`dirname $0`/.."

exit_code=0

if uv pip show -q black > /dev/null 2>&1; then
  echo -e "\nRunning black..."
  uv run black --check . || exit_code=1
fi

if uv pip show -q isort > /dev/null 2>&1; then
  echo -e "\nRunning isort..."
  uv run isort -c -q . || exit_code=1
fi

if uv pip show -q flake8 > /dev/null 2>&1; then
  echo -e "\nRunning flake8..."
  uv run flake8 || exit_code=1
fi

if uv pip show -q mypy > /dev/null 2>&1; then
  echo -e "\nRunning mypy..."
  uv run mypy . || exit_code=1
fi

if uv pip show -q pylint > /dev/null 2>&1; then
  echo -e "\nRunning pylint..."
  uv run pylint rtbhouse_sdk tests || exit_code=1
fi

exit $exit_code
