@echo off
setlocal

cd /d "%~dp0.."

if "%OPENAI_API_KEY%"=="" (
  echo Please set OPENAI_API_KEY to your DeepSeek API key first.
  exit /b 1
)

if "%OPENAI_API_BASE%"=="" (
  set "OPENAI_API_BASE=https://api.deepseek.com/v1"
)

if "%MODEL_NAME%"=="" (
  set "MODEL_NAME=deepseek-chat"
)

if "%LIMIT%"=="" (
  set "LIMIT=5"
)

set "PYTHONUTF8=1"

python run.py ^
  --scenario Scenario.CollaborativeConsultation ^
  --patient_database ./data/patients.json ^
  --doctor_database ./data/collaborative_doctors/doctors.json ^
  --patient Agent.Patient.GPT --patient_openai_model_name %MODEL_NAME% ^
  --reporter Agent.Reporter.GPT --reporter_openai_model_name %MODEL_NAME% ^
  --host Agent.Host.GPT --host_openai_model_name %MODEL_NAME% ^
  --number_of_doctors 3 ^
  --max_discussion_turn 2 ^
  --max_conversation_turn 1 ^
  --limit %LIMIT% ^
  --save_path outputs/collaboration_history_iiyi/deepseek_collaboration_final.jsonl ^
  --discussion_mode Parallel_with_Critique ^
  --ff_print
