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
    return _load_json(systems_root / system / f"{name}.json")


def save_system_config_text(systems_root: Path, system: str, name: str, text: str) -> None:
    if name not in CONFIG_NAMES:
        raise ValueError(f"不支援的設定類型：{name}")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("系統設定最外層必須是 JSON object")
    if data.get("system") != system:
        raise ValueError(f"設定內 system 必須是 {system}")
    path = systems_root / system / f"{name}.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"無法讀取系統設定 {path}：{error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"系統設定必須是 JSON object：{path}")
    return data
