from dataclasses import asdict, dataclass, field


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
    schema_version: int = 1

    @classmethod
    def from_dict(cls, data: dict) -> "Case":
        return cls(**{name: data[name] for name in cls.__dataclass_fields__ if name in data})

    def to_dict(self) -> dict:
        return asdict(self)
