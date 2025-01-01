from pytest import TestCase


class TestTLA(TestCase):

    def test_none(self):
        fixed = LLMResponseUtils.tla_fixer(None)
        self.assertEqual(None, fixed)

    def test_badtla(self):
        fixed = LLMResponseUtils.tla_fixer("Farts Farts Magic (FFG). FFG is.")
        self.assertEqual("Farts Farts Magic (FFM). FFM is.", fixed)
