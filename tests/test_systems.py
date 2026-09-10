import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from calibration_manager.systems.loader import load_system_config, load_systems, save_system_config_text


class SystemConfigTest(unittest.TestCase):
    def test_repository_system_configs_load(self):
        root = Path(__file__).parents[1] / "config" / "systems"
        systems = load_systems(root)
        self.assertEqual([item["code"] for item in systems], ["E05", "E07", "E27"])
        for system in systems:
            self.assertEqual(load_system_config(root, system["code"], "capability")["system"], system["code"])

    def test_editable_config_is_validated_and_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "E05"
            folder.mkdir()
            path = folder / "pricing.json"
            path.write_text('{"system":"E05","rules":[]}', encoding="utf-8")
            updated = {"system": "E05", "rules": [{"description": "人工輸入"}]}

            save_system_config_text(root, "E05", "pricing", json.dumps(updated))

            self.assertEqual(load_system_config(root, "E05", "pricing"), updated)
            with self.assertRaisesRegex(ValueError, "system 必須是 E05"):
                save_system_config_text(root, "E05", "pricing", '{"system":"E07"}')


if __name__ == "__main__":
    unittest.main()
