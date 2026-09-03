import importlib
import sys
from pathlib import Path
import unittest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import add, multiply

class TestCore(unittest.TestCase):
    def test_math(self):
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(multiply(4, 5), 20)

    def test_dynamic_runtime_hook(self):
        # Dynamic import: requires dynamic_plugin.py at runtime!
        mod = importlib.import_module("dynamic_plugin")
        self.assertEqual(mod.runtime_hook(), "active_runtime_hook")

    def test_runtime_reflection_plugin(self):
        # Reflection import using string concatenation - invisible to naive static scans!
        mod_name = "unreferenced" + "_" + "reflection" + "_" + "plugin"
        plugin = importlib.import_module(mod_name)
        self.assertEqual(plugin.dynamic_feature(), "critical_dynamic_result")

if __name__ == "__main__":
    unittest.main()
