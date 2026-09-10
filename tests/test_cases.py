import sys
import tempfile
import unittest
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from calibration_manager.cases.service import calibration_warning, create_case, save_case
from calibration_manager.cases.storage import delete_case, load_all_cases, load_case


class CaseStorageTest(unittest.TestCase):
    systems = {"E05", "E07", "E27"}

    def test_case_round_trip_and_next_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = create_case(root, "2026-09-09", "E07", self.systems)
            case.customer["name"] = "測試客戶"
            case.instrument.update({"model": "M1", "serial_number": "S1"})
            path = save_case(case, root)

            self.assertEqual(path, root / "E07" / "2026-E07-00001" / "case.json")
            self.assertEqual(load_case(path), case)
            self.assertEqual(load_all_cases(root), [case])
            self.assertEqual(
                create_case(root, "2026-10-01", "E07", self.systems).case_id,
                "2026-E07-00002",
            )
            self.assertEqual(
                create_case(root, "2027-01-01", "E07", self.systems).case_id,
                "2027-E07-00001",
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

            reservation = root / "cases" / "E27" / case.case_id / "reservation"
            self.assertEqual(
                {path.name for path in reservation.iterdir()},
                {"original.jpg", "parsed.json"},
            )
            self.assertFalse(staging.exists())

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

    def test_incompatible_or_unknown_case_data_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.json"
            path.write_text('{"case_id":"x","system":"E05","schema_version":2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schema_version"):
                load_case(path)
            path.write_text(
                '{"case_id":"x","system":"E05","schema_version":1,"future_data":{}}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "future_data"):
                load_case(path)

    def test_old_layout_is_safely_migrated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = create_case(root, "2026-09-09", "E27", self.systems)
            old = root / "2026" / "E27" / case.case_id
            old.mkdir(parents=True)
            (old / "case.json").write_text(
                json.dumps(case.to_dict(), ensure_ascii=False), encoding="utf-8"
            )
            (old / "evidence.bin").write_bytes(b"unchanged")

            self.assertEqual(load_all_cases(root), [case])

            new = root / "E27" / case.case_id
            self.assertFalse(old.exists())
            self.assertEqual((new / "evidence.bin").read_bytes(), b"unchanged")

    def test_old_layout_collision_keeps_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = create_case(root, "2026-09-09", "E27", self.systems)
            old = root / "2026" / "E27" / case.case_id
            old.mkdir(parents=True)
            (old / "case.json").write_text(json.dumps(case.to_dict()), encoding="utf-8")
            destination = root / "E27" / case.case_id
            destination.mkdir(parents=True)

            with self.assertRaisesRegex(FileExistsError, "目的地已存在"):
                load_all_cases(root)
            self.assertTrue((old / "case.json").exists())

    def test_delete_one_case_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = create_case(root, "2026-09-09", "E05", self.systems)
            save_case(first, root)
            second = create_case(root, "2026-09-10", "E05", self.systems)
            save_case(second, root)

            delete_case(root, first.case_id)

            self.assertEqual(load_all_cases(root), [second])


if __name__ == "__main__":
    unittest.main()
