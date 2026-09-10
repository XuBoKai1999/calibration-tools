import json
import re
import shutil
from pathlib import Path

from calibration_manager.cases.model import Case


CASE_ID_PATTERN = re.compile(r"^(\d{4})-([A-Z]\d{2})-(\d{5})$")


def case_file(cases_root: Path, case_id: str) -> Path:
    match = CASE_ID_PATTERN.fullmatch(case_id)
    if not match:
        raise ValueError(f"無效的 Case ID：{case_id}")
    year, system, _ = match.groups()
    return cases_root / year / system / case_id / "case.json"


def write_case(case: Case, cases_root: Path) -> Path:
    path = case_file(cases_root, case.case_id)
    if case.system != case.case_id.split("-")[1]:
        raise ValueError("Case ID 與校正系統不一致")
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, case.to_dict())
    return path


def load_case(path: Path) -> Case:
    case_json = path / "case.json" if path.is_dir() else path
    return Case.from_dict(json.loads(case_json.read_text(encoding="utf-8")))


def load_all_cases(cases_root: Path) -> list[Case]:
    if not cases_root.exists():
        return []
    return [load_case(path) for path in sorted(cases_root.glob("*/*/*/case.json"))]


def copy_reservation_into_case(case: Case, cases_root: Path, staging_dir: Path) -> None:
    destination = case_file(cases_root, case.case_id).parent / "reservation"
    destination.mkdir(exist_ok=True)
    for source in staging_dir.iterdir():
        if source.is_file():
            shutil.copy2(source, destination / source.name)


def _write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
