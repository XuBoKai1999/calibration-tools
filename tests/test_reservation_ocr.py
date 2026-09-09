import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from calibration_manager.intake.reservation import stage_reservation_photo


class ReservationOcrTest(unittest.TestCase):
    def test_example_reservation_photo(self):
        photo = Path(__file__).parents[1] / "20260907_154041.jpg"
        with tempfile.TemporaryDirectory() as directory:
            staging, draft = stage_reservation_photo(photo, Path(directory) / "inbox")
            fields = draft["fields"]
            self.assertEqual(fields["system"], "E27")
            self.assertEqual(fields["tax_id"], "16130084")
            self.assertEqual(fields["serial_number"], "30064-091")
            self.assertIn("矽片電阻", fields["instrument_name"])
            self.assertTrue((staging / "original.jpg").exists())
            self.assertTrue((staging / "parsed.json").exists())


if __name__ == "__main__":
    unittest.main()
