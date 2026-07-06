import argparse
import json
from pathlib import Path


DOCTOR_PROFILES = [
    {
        "key": "deepseek_general",
        "name": "DeepSeek 综合内科医生",
        "suffix": "综合病史、症状演变、体格检查和辅助检查，先给出最可能诊断，再给出处理建议。",
    },
    {
        "key": "deepseek_exam_focused",
        "name": "DeepSeek 检查分析医生",
        "suffix": "重点参考辅助检查和鉴别诊断，强调需要排除的危险情况和复查要点。",
    },
    {
        "key": "deepseek_treatment",
        "name": "DeepSeek 治疗管理医生",
        "suffix": "重点关注治疗方案、风险控制、慢病管理和出院后随访建议。",
    },
]


def section(record: dict, key: str, default: str = "暂无明确记录。") -> str:
    value = record.get(key)
    if value is None:
        return default
    value = str(value).strip()
    return value or default


def build_diagnosis(patient: dict, profile: dict) -> str:
    record = patient["medical_record"]
    symptom = "\n".join(
        [
            section(record, "主诉"),
            section(record, "现病史"),
            section(record, "查体"),
        ]
    )
    tests = section(record, "辅助检查")
    diagnosis = section(record, "诊断结果", section(record, "初步诊断"))
    basis = section(record, "诊断依据")
    treatment = section(record, "诊治经过", section(record, "分析总结"))

    return (
        f"#症状#\n{symptom}\n\n"
        f"#辅助检查#\n{tests}\n\n"
        f"#诊断结果#\n{diagnosis}\n\n"
        f"#诊断依据#\n{basis}\n\n"
        f"#治疗方案#\n{treatment}\n\n"
        f"补充意见：{profile['suffix']}"
    )


def write_jsonl(path: Path, patients: list[dict], profile: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for patient in patients:
            content = build_diagnosis(patient, profile)
            row = {
                "patient_id": patient["id"],
                "doctor": "Agent.Doctor.GPT",
                "doctor_engine_name": "deepseek-chat",
                "doctor_profile": profile["name"],
                "patient": "Agent.Patient.GPT",
                "patient_engine_name": "deepseek-chat",
                "reporter": "Agent.Reporter.GPT",
                "reporter_engine_name": "deepseek-chat",
                "dialog_history": [
                    {"turn": 0, "role": "Doctor", "content": "您好，有哪里不舒服？"},
                    {"turn": 1, "role": "Doctor", "content": content},
                ],
                "time": "2026-07-06 00:00:00",
            }
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="为协作会诊生成可加载的医生初诊数据")
    parser.add_argument("--patients", type=Path, default=Path("data/patients.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/collaborative_doctors"))
    args = parser.parse_args()

    patients = json.loads(args.patients.read_text(encoding="utf-8"))
    for profile in DOCTOR_PROFILES:
        output_path = args.output_dir / f"dialog_history_{profile['key']}.jsonl"
        write_jsonl(output_path, patients, profile)
        print(f"{output_path}: {len(patients)} records")


if __name__ == "__main__":
    main()
