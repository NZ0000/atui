import unittest
import os
import importlib.util

class TestPropsModule(unittest.TestCase):
    def test_props_file_exists(self):
        self.assertTrue(os.path.exists("modules/props.js"), "modules/props.js should exist")

    def test_props_syntax_and_structure(self):
        with open("modules/props.js", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("class Props", content)
        self.assertIn("addTo", content)
        self.assertIn("update", content)
        self.assertIn("PointLight", content)

if __name__ == "__main__":
    unittest.main()
