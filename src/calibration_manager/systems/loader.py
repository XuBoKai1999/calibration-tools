import json
from pathlib import Path


CONFIG_NAMES = ("capability", "pricing", "measurement_schema")


def load_systems(systems_root: Path) -> list[dict]:
    if not systems_root.exists():
        return []
    systems = []
    for path in sorted(systems_root.glob("*/system.json")):
        data = _load_json(path)
        if data.get("code") != path.parent.name or not data.get("name"):
            raise ValueError(f"無效的系統設定：{path}")
        systems.append(data)
    return systems


def load_system_config(systems_root: Path, system: str, name: str) -> dict:
    if name not in CONFIG_NAMES:
        raise ValueError(f"不支援的設定類型：{name}")
    data = _load_json(systems_root / system / f"{name}.json")
    validate_system_config(name, data, system)
    return data


def save_system_config_text(systems_root: Path, system: str, name: str, text: str) -> None:
    if name not in CONFIG_NAMES:
        raise ValueError(f"不支援的設定類型：{name}")
    data = json.loads(text)
    validate_system_config(name, data, system)
    path = systems_root / system / f"{name}.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def validate_system_config(name: str, data: dict, system: str) -> None:
    if not isinstance(data, dict):
        raise ValueError("系統設定最外層必須是 JSON object")
    if data.get("schema_version") != 1:
        raise ValueError("系統設定 schema_version 必須是 1")
    if data.get("system") != system:
        raise ValueError(f"設定內 system 必須是 {system}")
    if not isinstance(data.get("notes"), str):
        raise ValueError("系統設定 notes 必須是字串")

    list_key = {"capability": "ranges", "pricing": "rules", "measurement_schema": "columns"}[name]
    entries = data.get(list_key)
    if not isinstance(entries, list) or not all(isinstance(item, dict) for item in entries):
        raise ValueError(f"{list_key} 必須是 JSON object 陣列")
    if name == "pricing" and not isinstance(data.get("currency"), str):
        raise ValueError("pricing currency 必須是字串")
    if name == "measurement_schema" and any(
        not isinstance(item.get("name"), str) or not isinstance(item.get("type"), str)
        for item in entries
    ):
        raise ValueError("measurement_schema 每個 column 都必須有字串 name 與 type")


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"無法讀取系統設定 {path}：{error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"系統設定必須是 JSON object：{path}")
    return data
