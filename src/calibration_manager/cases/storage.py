import json
import hashlib
import re
import shutil
from pathlib import Path

from calibration_manager.cases.model import Case


CASE_ID_PATTERN = re.compile(r"^(\d{4})-([A-Z]\d{2})-(\d{5})$")


def case_file(cases_root: Path, case_id: str) -> Path:
    match = CASE_ID_PATTERN.fullmatch(case_id)
    if not match:
        raise ValueError(f"無效的 Case ID：{case_id}")
    _, system, _ = match.groups()
    return cases_root / system / case_id / "case.json"


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
    migrate_old_cases(cases_root)
    return [load_case(path) for path in sorted(cases_root.glob("*/*/case.json"))]


def migrate_old_cases(cases_root: Path) -> list[Path]:
    migrated = []
    for case_json in sorted(cases_root.glob("[0-9][0-9][0-9][0-9]/*/*/case.json")):
        source = case_json.parent
        case = load_case(case_json)
        match = CASE_ID_PATTERN.fullmatch(case.case_id)
        if not match or case.system != match.group(2) or source.parent.name != case.system:
            raise ValueError(f"舊案件路徑與內容不一致：{source}")
        destination = case_file(cases_root, case.case_id).parent
        if source == destination:
            continue
        if destination.exists():
            raise FileExistsError(f"舊案件移轉目的地已存在，未移動來源：{destination}")
        temporary = destination.with_name(destination.name + ".migrating")
        if temporary.exists():
            raise FileExistsError(f"舊案件移轉暫存目錄已存在：{temporary}")
        temporary.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copytree(source, temporary)
            if _directory_digest(source) != _directory_digest(temporary):
                raise OSError(f"舊案件複製驗證失敗：{source}")
            temporary.replace(destination)
        except Exception:
            if temporary.exists():
                shutil.rmtree(temporary)
            raise
        shutil.rmtree(source)
        migrated.append(destination)
    return migrated


def delete_case(cases_root: Path, case_id: str) -> None:
    directory = case_file(cases_root, case_id).parent
    if not directory.is_dir():
        raise FileNotFoundError(f"找不到案件：{case_id}")
    shutil.rmtree(directory)


def copy_reservation_into_case(case: Case, cases_root: Path, staging_dir: Path) -> None:
    destination = case_file(cases_root, case.case_id).parent / "reservation"
    destination.mkdir(parents=True, exist_ok=True)
    for source in staging_dir.iterdir():
        if source.is_file():
            shutil.copy2(source, destination / source.name)


def _write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _directory_digest(directory: Path) -> list[tuple[str, str]]:
    return [
        (str(path.relative_to(directory)), hashlib.sha256(path.read_bytes()).hexdigest())
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    ]
