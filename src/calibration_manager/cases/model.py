from dataclasses import asdict, dataclass, field


SUPPORTED_SCHEMA_VERSION = 1


@dataclass
class Case:
    case_id: str
    system: str
    status: str = "reserved"
    customer: dict = field(default_factory=dict)
    instrument: dict = field(default_factory=dict)
    schedule: dict = field(default_factory=dict)
    report: dict = field(default_factory=lambda: {
        "previous_report_number": "", "current_report_number": "", "notes": []
    })
    calibration_request: dict = field(default_factory=lambda: {
        "mode": "unspecified", "reference_report": None, "points": [], "notes": ""
    })
    schema_version: int = SUPPORTED_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, data: dict) -> "Case":
        version = data.get("schema_version", 1)
        if version != SUPPORTED_SCHEMA_VERSION:
            raise ValueError(f"不支援的 Case schema_version：{version}")
        unknown = set(data) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"Case 含有目前版本不認識的欄位：{', '.join(sorted(unknown))}")
        return cls(**data)

    def to_dict(self) -> dict:
        return asdict(self)
