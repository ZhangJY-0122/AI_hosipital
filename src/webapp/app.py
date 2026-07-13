from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field


SRC_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = SRC_DIR.parent
PATIENTS_PATH = SRC_DIR / "data" / "patients.json"
RESULTS_PATH = SRC_DIR / "outputs" / "dialog_history_iiyi" / "deepseek_consultation_dialog_history.jsonl"
FRONTEND_DIST = PROJECT_DIR / "web" / "dist"

_cases_cache: Optional[List[Dict[str, Any]]] = None
_jobs: Dict[str, Dict[str, Any]] = {}
_jobs_lock = threading.Lock()
STOP_CHARS = set("的一是在不了和有就都而及与或为等这那您你我他她它患者医生情况症状需要可以")
QUERY_EXPANSIONS = [
    (("缓不上气", "喘不上气", "喘不过气", "呼吸不畅", "憋气", "气不够用"), " 胸闷 气短 气促 呼吸困难 喘息"),
    (("胸口发闷", "胸口闷", "胸发闷"), " 胸闷 胸痛 心慌 气短"),
    (("心跳快", "心慌", "心脏咚咚"), " 心悸 心律失常 胸闷 气短"),
]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: List[ChatMessage] = Field(default_factory=list)
    top_k: int = Field(default=3, ge=1, le=5)


class RunRequest(BaseModel):
    limit: int = Field(default=5, ge=1, le=606)


def load_cases() -> List[Dict[str, Any]]:
    global _cases_cache
    if _cases_cache is None:
        _cases_cache = json.loads(PATIENTS_PATH.read_text(encoding="utf-8"))
    return _cases_cache


def normalize_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def case_text(case: Dict[str, Any]) -> str:
    record = case.get("medical_record", {})
    fields = [
        case.get("title"),
        case.get("department"),
        case.get("diseases"),
        record.get("主诉"),
        record.get("现病史"),
        record.get("既往史"),
        record.get("查体"),
        record.get("辅助检查"),
        record.get("诊断结果") or record.get("初步诊断"),
    ]
    return normalize_text(" ".join(normalize_text(item) for item in fields))


def tokenize(text: str) -> Counter:
    text = normalize_text(text).lower()
    latin = re.findall(r"[a-z0-9]+", text)
    chinese_sequences = re.findall(r"[\u4e00-\u9fff]+", text)
    chinese_bigrams = [
        sequence[index : index + 2]
        for sequence in chinese_sequences
        for index in range(len(sequence) - 1)
        if sequence[index] not in STOP_CHARS and sequence[index + 1] not in STOP_CHARS
    ]
    chunks = latin + chinese_bigrams
    return Counter(chunks)


def expand_query(query: str) -> str:
    expanded = query
    for triggers, extra_terms in QUERY_EXPANSIONS:
        if any(trigger in query for trigger in triggers):
            expanded += extra_terms
    return expanded


def summarize_case(case: Dict[str, Any], score: float = 0.0) -> Dict[str, Any]:
    record = case.get("medical_record", {})
    return {
        "id": case.get("id"),
        "title": normalize_text(case.get("title")),
        "department": normalize_text(case.get("department")),
        "diseases": normalize_text(case.get("diseases")),
        "chief_complaint": normalize_text(record.get("主诉")),
        "history": normalize_text(record.get("现病史")),
        "exam": normalize_text(record.get("查体")),
        "tests": normalize_text(record.get("辅助检查")),
        "diagnosis": normalize_text(record.get("诊断结果") or record.get("初步诊断")),
        "score": round(score, 4),
    }


def retrieve_cases(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    query_tokens = tokenize(expand_query(query))
    if not query_tokens:
        return []

    scored = []
    query_size = max(sum(query_tokens.values()), 1)
    for case in load_cases():
        tokens = tokenize(case_text(case))
        overlap = sum((query_tokens & tokens).values())
        if overlap < 2:
            continue
        score = overlap / query_size
        if score < 0.18:
            continue
        scored.append((score, case))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [summarize_case(case, score) for score, case in scored[:limit]]


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not set in the backend environment.")

    base_url = os.getenv("OPENAI_API_BASE")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def build_case_context(matches: List[Dict[str, Any]]) -> str:
    blocks = []
    for index, match in enumerate(matches, start=1):
        blocks.append(
            "\n".join(
                [
                    f"相似病例 {index}: {match['title'] or match['department']}",
                    f"主诉: {match['chief_complaint'] or '无'}",
                    f"现病史: {match['history'] or '无'}",
                    f"查体: {match['exam'] or '无'}",
                    f"辅助检查: {match['tests'] or '无'}",
                    f"诊断参考: {match['diagnosis'] or '无'}",
                ]
            )
        )
    return "\n\n".join(blocks)


def read_results(limit: int = 50) -> List[Dict[str, Any]]:
    if not RESULTS_PATH.exists():
        return []

    rows: List[Dict[str, Any]] = []
    with RESULTS_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))

    rows = rows[-limit:]
    formatted = []
    for row in reversed(rows):
        dialog = row.get("dialog_history", [])
        final = dialog[-1].get("content", "") if dialog else ""
        formatted.append(
            {
                "patient_id": row.get("patient_id"),
                "doctor": row.get("doctor_engine_name"),
                "patient": row.get("patient_engine_name"),
                "time": row.get("time"),
                "turns": len(dialog),
                "final": final,
            }
        )
    return formatted


def run_consultation_job(job_id: str, limit: int) -> None:
    with _jobs_lock:
        _jobs[job_id].update({"status": "running", "started_at": time.strftime("%Y-%m-%d %H:%M:%S")})

    env = os.environ.copy()
    env["LIMIT"] = str(limit)
    env["PYTHON_BIN"] = sys.executable
    command = [str(SRC_DIR / "scripts" / "run_deepseek_consultation.sh")]

    try:
        result = subprocess.run(
            command,
            cwd=str(PROJECT_DIR),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=600,
            check=False,
        )
        with _jobs_lock:
            _jobs[job_id].update(
                {
                    "status": "completed" if result.returncode == 0 else "failed",
                    "return_code": result.returncode,
                    "output": result.stdout[-6000:],
                    "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    except Exception as exc:
        with _jobs_lock:
            _jobs[job_id].update(
                {
                    "status": "failed",
                    "return_code": None,
                    "output": str(exc),
                    "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )


app = FastAPI(title="AI Hospital Web API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "model": os.getenv("MODEL_NAME", "deepseek-chat"),
        "api_base": os.getenv("OPENAI_API_BASE", ""),
        "has_api_key": bool(os.getenv("OPENAI_API_KEY")),
        "case_count": len(load_cases()),
        "result_count": len(read_results(limit=10000)),
    }


@app.get("/api/cases")
def list_cases(
    q: str = "",
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    cases = load_cases()
    if q.strip():
        query = q.strip().lower()
        filtered = [
            case
            for case in cases
            if query in case_text(case).lower()
        ]
    else:
        filtered = cases

    page = filtered[offset : offset + limit]
    return {
        "total": len(filtered),
        "items": [summarize_case(case) for case in page],
    }


@app.get("/api/cases/search")
def search_cases(q: str, limit: int = Query(default=5, ge=1, le=10)) -> Dict[str, Any]:
    return {"items": retrieve_cases(q, limit)}


@app.get("/api/results")
def list_results(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    return {
        "path": str(RESULTS_PATH.relative_to(PROJECT_DIR)),
        "items": read_results(limit),
    }


@app.post("/api/chat")
def chat(request: ChatRequest) -> Dict[str, Any]:
    matches = retrieve_cases(request.message, request.top_k)
    context = build_case_context(matches)
    model = os.getenv("MODEL_NAME", "deepseek-chat")

    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "你是一个谨慎、专业、表达清晰的 AI 医生助手。"
                "你可以参考相似病例，但不能把参考病例当成用户本人已经确诊。"
                "回答必须控制在 800 个汉字以内。"
                "不要使用星号加粗，不要输出 ** 或 *。"
                "固定使用这些二级标题："
                "## 需要先确认的问题\n## 初步风险分层\n## 可能方向\n## 建议检查\n## 下一步。"
                "每个标题下面只用短句项目符号，每栏最多 4 条。"
                "如果用户信息很少，先少量追问，不要展开成长篇科普。"
                "遇到胸痛、呼吸困难、意识障碍、剧烈腹痛、大出血、卒中征象等急症时，"
                "要明确建议立即线下急诊。不要替代真实医生诊疗。"
            ),
        }
    ]
    if context:
        messages.append({"role": "system", "content": f"病例库检索参考:\n{context}"})

    for item in request.history[-12:]:
        if item.role in {"user", "assistant"} and item.content.strip():
            messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": request.message})

    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=1600,
    )
    return {
        "reply": response.choices[0].message.content,
        "references": matches,
        "model": model,
    }


@app.post("/api/runs")
def start_run(request: RunRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    job_id = uuid.uuid4().hex[:12]
    with _jobs_lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "limit": request.limit,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "output": "",
        }
    background_tasks.add_task(run_consultation_job, job_id, request.limit)
    return _jobs[job_id]


@app.get("/api/runs/{job_id}")
def get_run(job_id: str) -> Dict[str, Any]:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


@app.get("/{path:path}")
def serve_frontend(path: str) -> FileResponse:
    index_path = FRONTEND_DIST / "index.html"
    target = FRONTEND_DIST / path
    if path and target.exists() and target.is_file():
        return FileResponse(target)
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend is not built. Run pnpm build in web/.")
