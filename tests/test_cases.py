import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from calibration_manager.cases.service import create_case, save_case
from calibration_manager.cases.storage import load_all_cases, load_case


class CaseStorageTest(unittest.TestCase):
    def test_case_round_trip_and_next_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = create_case(root, "2026-09-09", "E07")
            case.customer["name"] = "測試客戶"
            case.instrument.update({"model": "M1", "serial_number": "S1"})
            path = save_case(case, root)

            self.assertEqual(path, root / "2026" / "E07" / "2026-E07-00001" / "case.json")
            self.assertEqual(load_case(path), case)
            self.assertEqual(load_all_cases(root), [case])
            self.assertEqual(create_case(root, "2026-10-01", "E07").case_id, "2026-E07-00002")
            self.assertEqual({item.name for item in path.parent.iterdir()}, {"case.json"})

    def test_confirmed_reservation_is_copied_into_case(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = root / "inbox" / "draft-id"
            staging.mkdir(parents=True)
            (staging / "original.jpg").write_bytes(b"photo")
            (staging / "parsed.json").write_text("{}", encoding="utf-8")
            case = create_case(root / "cases", "2026-09-09", "E27")

            save_case(case, root / "cases", staging)

            reservation = root / "cases" / "2026" / "E27" / case.case_id / "reservation"
            self.assertEqual(
                {path.name for path in reservation.iterdir()},
                {"original.jpg", "parsed.json"},
            )


if __name__ == "__main__":
    unittest.main()
