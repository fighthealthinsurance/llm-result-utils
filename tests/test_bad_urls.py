from unittest import TestCase
from llm_result_utils.cleaner_utils import CleanerUtils

class TestBadURLs(TestCase):

    def test_none(self):
        fixed = CleanerUtils.url_fixer(None)
        self.assertEqual(None, fixed)

    def test_badtla(self):
        # This will break if google adds a fart page but ehhh seams legit
        fixed = CleanerUtils.url_fixer("http://www.google.com http://www.google.com/farts")
        self.assertEqual("http://www.google.com ", fixed)
