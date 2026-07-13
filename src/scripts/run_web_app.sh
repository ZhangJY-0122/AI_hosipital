#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_DIR="$(cd "${SRC_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${PROJECT_DIR}/.venv/bin/python}"

if [[ "${PYTHON_BIN}" != /* ]]; then
  PYTHON_BIN="${PROJECT_DIR}/${PYTHON_BIN}"
fi

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python interpreter not found or not executable: ${PYTHON_BIN}" >&2
  exit 1
fi

cd "${PROJECT_DIR}"
export PYTHONPATH="${SRC_DIR}:${PYTHONPATH:-}"

if [[ "${RELOAD:-0}" == "1" ]]; then
  "${PYTHON_BIN}" -m uvicorn webapp.app:app --app-dir src --host 127.0.0.1 --port "${PORT:-8000}" --reload
else
  "${PYTHON_BIN}" -m uvicorn webapp.app:app --app-dir src --host 127.0.0.1 --port "${PORT:-8000}"
fi
