import argparse
import json
from pathlib import Path


REQUIRED_FIELDS = ("id", "profile", "medical_record")


def load_json_without_bom(path: Path):
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("文件包含 UTF-8 BOM，请另存为无 BOM 的 UTF-8")
    return json.loads(raw.decode("utf-8"))


def validate_patient_database(path: Path) -> int:
    data = load_json_without_bom(path)
    if not isinstance(data, list):
        raise ValueError("病例库最外层必须是 JSON 数组，例如 [{...}]")

    errors = []
    for index, patient in enumerate(data):
        if not isinstance(patient, dict):
            errors.append(f"第 {index + 1} 条病例不是对象")
            continue

        for field in REQUIRED_FIELDS:
            if field not in patient:
                errors.append(f"第 {index + 1} 条病例缺少字段: {field}")

        medical_record = patient.get("medical_record")
        if medical_record is not None and not isinstance(medical_record, dict):
            errors.append(f"第 {index + 1} 条病例的 medical_record 必须是对象")

    if errors:
        raise ValueError("\n".join(errors))
    return len(data)


def main():
    parser = argparse.ArgumentParser(description="校验 AI Hospital 病例 JSON 格式")
    parser.add_argument("path", type=Path, help="病例 JSON 文件路径")
    args = parser.parse_args()

    count = validate_patient_database(args.path)
    print(f"OK: {args.path} 包含 {count} 条病例")


if __name__ == "__main__":
    main()
