#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_DIR="$(cd "${SRC_DIR}/.." && pwd)"

cd "${SRC_DIR}"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "Please set OPENAI_API_KEY to your DeepSeek API key first." >&2
  echo 'Example: export OPENAI_API_KEY="your_deepseek_key"' >&2
  exit 1
fi

export OPENAI_API_BASE="${OPENAI_API_BASE:-https://api.deepseek.com/v1}"
MODEL_NAME="${MODEL_NAME:-deepseek-chat}"
LIMIT="${LIMIT:-5}"
PYTHON_BIN="${PYTHON_BIN:-${PROJECT_DIR}/.venv/bin/python}"
export PYTHONUTF8=1

if [[ "${PYTHON_BIN}" != /* ]]; then
  PYTHON_BIN="${PROJECT_DIR}/${PYTHON_BIN}"
fi

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python interpreter not found or not executable: ${PYTHON_BIN}" >&2
  echo "Create the virtual environment first: python3 -m venv .venv" >&2
  exit 1
fi

"${PYTHON_BIN}" run.py \
  --patient_database ./data/patients.json \
  --doctor Agent.Doctor.GPT --doctor_openai_model_name "${MODEL_NAME}" \
  --patient Agent.Patient.GPT --patient_openai_model_name "${MODEL_NAME}" \
  --reporter Agent.Reporter.GPT --reporter_openai_model_name "${MODEL_NAME}" \
  --save_path outputs/dialog_history_iiyi/deepseek_consultation_dialog_history.jsonl \
  --limit "${LIMIT}" \
  --max_conversation_turn 1 \
  --ff_print
