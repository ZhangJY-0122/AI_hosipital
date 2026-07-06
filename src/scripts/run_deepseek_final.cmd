@echo off
setlocal

cd /d "%~dp0.."

if "%OPENAI_API_KEY%"=="" (
  echo Please set OPENAI_API_KEY to your DeepSeek API key first.
  echo Example: set "OPENAI_API_KEY=your_deepseek_key"
  exit /b 1
)

if "%OPENAI_API_BASE%"=="" (
  set "OPENAI_API_BASE=https://api.deepseek.com/v1"
)

if "%MODEL_NAME%"=="" (
  set "MODEL_NAME=deepseek-chat"
)

set "PYTHONUTF8=1"

python run.py ^
  --patient_database ./data/patients.json ^
  --doctor Agent.Doctor.GPT --doctor_openai_model_name %MODEL_NAME% ^
  --patient Agent.Patient.GPT --patient_openai_model_name %MODEL_NAME% ^
  --reporter Agent.Reporter.GPT --reporter_openai_model_name %MODEL_NAME% ^
  --save_path outputs/dialog_history_iiyi/dialog_history_deepseek_final.jsonl ^
  --max_conversation_turn 1 ^
  --ff_print
