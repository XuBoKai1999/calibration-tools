from pathlib import Path

from calibration_manager.cases.model import Case
from calibration_manager.cases.storage import (
    CASE_ID_PATTERN,
    case_file,
    copy_reservation_into_case,
    load_case,
    write_case,
)


def create_case(cases_root: Path, date: str, system: str, supported_systems: set[str]) -> Case:
    if system not in supported_systems:
        raise ValueError(f"不支援的校正系統：{system}")
    year = date[:4]
    numbers = []
    system_dir = cases_root / year / system
    if system_dir.exists():
        for path in system_dir.iterdir():
            match = CASE_ID_PATTERN.fullmatch(path.name)
            if match:
                numbers.append(int(match.group(3)))
    case_id = f"{year}-{system}-{max(numbers, default=0) + 1:05d}"
    return Case(case_id=case_id, system=system, schedule={
        "reserved_date": date, "received_date": None, "completed_date": None
    })


def save_case(case: Case, cases_root: Path, reservation_staging: Path | None = None) -> Path:
    _set_calibration_source(case)
    path = write_case(case, cases_root)
    if reservation_staging:
        copy_reservation_into_case(case, cases_root, reservation_staging)
    return path


def load_case_by_id(cases_root: Path, case_id: str) -> Case:
    return load_case(case_file(cases_root, case_id))


def calibration_warning(case: Case) -> str:
    if case.calibration_request.get("points"):
        return ""
    if case.report.get("previous_report_number"):
        return "尚未取得本次校正點；請從前次報告匯入或人工確認。"
    return "本次與前次校正點皆未提供；請向使用者確認校正點。"


def _set_calibration_source(case: Case) -> None:
    request = case.calibration_request
    if request.get("points"):
        request["mode"] = "specified_points"
        request["reference_report"] = None
    elif case.report.get("previous_report_number"):
        request["mode"] = "previous_report"
        request["reference_report"] = case.report["previous_report_number"]
    else:
        request["mode"] = "unspecified"
        request["reference_report"] = None
