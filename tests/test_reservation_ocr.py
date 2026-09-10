import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from calibration_manager.intake.reservation import Token, parse_reservation_tokens


class ReservationOcrTest(unittest.TestCase):
    def test_parser_uses_only_confident_tokens(self):
        fields = parse_reservation_tokens([
            Token("E240540A", 0, 0, 100, 20, 0.98),
            Token("12345678", 0, 30, 100, 50, 0.42),
        ])

        self.assertEqual(fields["previous_report_number"], "E240540A")
        self.assertEqual(fields["tax_id"], "")


if __name__ == "__main__":
    unittest.main()
