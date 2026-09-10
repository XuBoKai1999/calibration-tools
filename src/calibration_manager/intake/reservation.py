import json
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from calibration_manager.intake.ocr import parse_image


MIN_AUTO_FILL_CONFIDENCE = 0.6


@dataclass(frozen=True)
class Token:
    text: str
    left: float
    top: float
    right: float
    bottom: float
    confidence: float = 1.0

    @property
    def center_y(self) -> float:
        return (self.top + self.bottom) / 2


def stage_reservation_photo(image_path: Path, inbox_root: Path) -> tuple[Path, dict]:
    ocr_result = parse_image(image_path)
    draft = {
        "source_name": image_path.name,
        "raw_text": ocr_result["raw_text"],
        "mean_confidence": ocr_result["mean_confidence"],
        "fields": parse_reservation_tokens(_tokens_from_ocr(ocr_result)),
    }
    staging_dir = inbox_root / uuid.uuid4().hex
    staging_dir.mkdir(parents=True)
    shutil.copy2(image_path, staging_dir / f"original{image_path.suffix.lower()}")
    _write_json(staging_dir / "parsed.json", draft)
    return staging_dir, draft


def parse_reservation_tokens(tokens: list[Token]) -> dict:
    tokens = [token for token in tokens if token.confidence >= MIN_AUTO_FILL_CONFIDENCE]
    if not tokens:
        return {}
    width = max(token.right for token in tokens)

    def first(label: str) -> Token | None:
        return next((token for token in tokens if label in token.text), None)

    def right_of(label: str, max_x: float = float("inf")) -> str:
        anchor = first(label)
        if not anchor:
            return ""
        candidates = [
            token for token in tokens
            if token.left >= anchor.right - 10
            and token.left < max_x
            and abs(token.center_y - anchor.center_y) <= max(55, anchor.bottom - anchor.top)
        ]
        return min(
            candidates,
            key=lambda token: abs(token.center_y - anchor.center_y) * 5 + token.left - anchor.right,
        ).text if candidates else ""

    def phone_right_of(label: str) -> str:
        anchor = first(label)
        if not anchor:
            return ""
        candidates = [
            token for token in tokens
            if token.left >= anchor.right - 10
            and abs(token.center_y - anchor.center_y) < 80
            and len(re.sub(r"\D", "", token.text)) >= 7
        ]
        return min(candidates, key=lambda token: abs(token.center_y - anchor.center_y)).text \
            if candidates else ""

    raw_text = "\n".join(token.text for token in tokens)
    date_match = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", raw_text)
    report_match = re.search(r"\bE\d{6}[A-Z]?\b", raw_text, re.IGNORECASE)
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", raw_text)
    postal_code = next((token.text for token in tokens if re.fullmatch(r"\d{3}-\d{2}", token.text)), "")
    customer_label = first("顧客名稱")
    customer_candidates = [
        token for token in tokens
        if customer_label
        and token.left > customer_label.right
        and token.left < width * 0.48
        and 0 < customer_label.center_y - token.center_y < 70
    ]
    tax_id = next((token.text for token in tokens if re.fullmatch(r"\d{8}", token.text)), "")

    address_label = first("顧客地址")
    note = first("註：")
    address = ""
    if address_label and note:
        address_parts = [
            token.text for token in tokens
            if token.left > address_label.right
            and token.left < width * 0.48
            and address_label.top - 20 <= token.center_y < note.top
        ]
        address = "".join(address_parts)

    headers = ("預約件名稱", "廠牌/型號", "校正／", "預定校正")
    item_name = _table_column(tokens, headers, 0, "特殊預約件")
    identity = _table_column(tokens, headers, 1, "特殊預約件")
    calibration = _table_column(tokens, headers, 2, "特殊預約件")
    identity_parts = [part.strip() for part in identity.split("/") if part.strip()]

    return {
        "request_date": "-".join((date_match.group(1), date_match.group(2).zfill(2),
                                   date_match.group(3).zfill(2))) if date_match else "",
        "system": "E27" if "電阻" in item_name or "矽片" in item_name else "",
        "customer_name": min(customer_candidates, key=lambda token: token.left).text
        if customer_candidates else "",
        "tax_id": tax_id,
        "contact": right_of("聯絡人"),
        "phone": phone_right_of("聯絡電話"),
        "fax": phone_right_of("傳真號碼"),
        "postal_code": postal_code,
        "email": re.sub(r"\.{2,}", ".", email_match.group(0)) if email_match else "",
        "address": address,
        "instrument_name": item_name,
        "brand": identity_parts[0] if len(identity_parts) >= 2 else "",
        "model": identity_parts[-2] if len(identity_parts) >= 2 else identity,
        "serial_number": identity_parts[-1] if len(identity_parts) >= 2 else "",
        "calibration_notes": calibration,
        "previous_report_number": report_match.group(0).upper() if report_match else "",
    }


def _tokens_from_ocr(result: dict) -> list[Token]:
    tokens = []
    for item in result["tokens"]:
        box = item["box"]
        tokens.append(Token(item["text"], min(p[0] for p in box), min(p[1] for p in box),
                            max(p[0] for p in box), max(p[1] for p in box),
                            float(item.get("confidence", 0))))
    return tokens


def discard_reservation_staging(staging_dir: Path, inbox_root: Path) -> None:
    staging = staging_dir.resolve()
    inbox = inbox_root.resolve()
    if staging.parent != inbox:
        raise ValueError("拒絕刪除 inbox 以外的暫存資料")
    if staging.exists():
        shutil.rmtree(staging)


def _table_column(tokens: list[Token], labels: tuple[str, ...], index: int, end_label: str) -> str:
    headers = [next((token for token in tokens if label in token.text), None) for label in labels]
    start = headers[index]
    end = next((token for token in tokens if end_label in token.text), None)
    if not start or not end or any(header is None for header in headers):
        return ""
    left = 0 if index == 0 else (headers[index - 1].right + headers[index].left) / 2
    right = float("inf") if index == len(headers) - 1 else (headers[index].right + headers[index + 1].left) / 2
    values = [
        token for token in tokens
        if left <= (token.left + token.right) / 2 < right
        and start.bottom < token.center_y < end.top
    ]
    return " ".join(token.text for token in sorted(values, key=lambda token: (token.top, token.left)))


def _write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
