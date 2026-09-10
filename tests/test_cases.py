import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from calibration_manager.cases.service import calibration_warning, create_case, save_case
from calibration_manager.cases.storage import load_all_cases, load_case


class CaseStorageTest(unittest.TestCase):
    systems = {"E05", "E07", "E27"}

    def test_case_round_trip_and_next_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = create_case(root, "2026-09-09", "E07", self.systems)
            case.customer["name"] = "測試客戶"
            case.instrument.update({"model": "M1", "serial_number": "S1"})
            path = save_case(case, root)

            self.assertEqual(path, root / "2026" / "E07" / "2026-E07-00001" / "case.json")
            self.assertEqual(load_case(path), case)
            self.assertEqual(load_all_cases(root), [case])
            self.assertEqual(
                create_case(root, "2026-10-01", "E07", self.systems).case_id,
                "2026-E07-00002",
            )
            self.assertEqual({item.name for item in path.parent.iterdir()}, {"case.json"})

    def test_confirmed_reservation_is_copied_into_case(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = root / "inbox" / "draft-id"
            staging.mkdir(parents=True)
            (staging / "original.jpg").write_bytes(b"photo")
            (staging / "parsed.json").write_text("{}", encoding="utf-8")
            case = create_case(root / "cases", "2026-09-09", "E27", self.systems)

            save_case(case, root / "cases", staging)

            reservation = root / "cases" / "2026" / "E27" / case.case_id / "reservation"
            self.assertEqual(
                {path.name for path in reservation.iterdir()},
                {"original.jpg", "parsed.json"},
            )

    def test_unknown_system_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "不支援"):
                create_case(Path(directory), "2026-09-09", "E99", self.systems)

    def test_calibration_point_source_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = create_case(root, "2026-09-09", "E27", self.systems)
            self.assertIn("皆未提供", calibration_warning(case))

            case.report["previous_report_number"] = "E240540A"
            save_case(case, root)
            self.assertEqual(case.calibration_request["mode"], "previous_report")
            self.assertEqual(case.calibration_request["reference_report"], "E240540A")
            self.assertIn("前次報告", calibration_warning(case))

            case.calibration_request["points"] = ["100 Ω"]
            save_case(case, root)
            self.assertEqual(case.calibration_request["mode"], "specified_points")
            self.assertEqual(calibration_warning(case), "")


if __name__ == "__main__":
    unittest.main()
