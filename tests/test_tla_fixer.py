import unittest
from llm_result_utils.cleaner_utils import CleanerUtils

class TestTLA(unittest.TestCase):

    def test_none(self):
        fixed = CleanerUtils.tla_fixer(None)
        self.assertEqual(None, fixed)

    def test_badtla(self):
        fixed = CleanerUtils.tla_fixer("Farts Farts Magic (FFG). FFG is.")
        self.assertEqual("Farts Farts Magic (FFM). FFM is.", fixed)
