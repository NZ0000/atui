import unittest
import os
import importlib.util

class TestTerrainModule(unittest.TestCase):
    def test_terrain_module_exists_and_syntax(self):
        # Verify terrain.js exists
        terrain_path = os.path.join("modules", "terrain.js")
        self.assertTrue(os.path.exists(terrain_path), f"modules/terrain.js must exist")
        
        # Read file contents and check for expected class structure and methods
        with open(terrain_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("class Terrain", content)
        self.assertIn("constructor(", content)
        self.assertIn("addTo(", content)
        self.assertIn("update(", content)
        self.assertIn("createProceduralNormalMap", content)
        self.assertIn("createProceduralRoughnessMap", content)

if __name__ == "__main__":
    unittest.main()
