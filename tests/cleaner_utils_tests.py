import unittest
from cleaner_utils import CleanerUtils

class TestCleanerUtils(unittest.TestCase):
    def test_tla_fixer(self):
        result = "Approved for Patient J R T (JRT)"
        fixed_result = CleanerUtils.tla_fixer(result)
        self.assertEqual(fixed_result, "Approved for Patient J R T (JRT)")

        result = "Approved for Patient J R T (ABC)"
        fixed_result = CleanerUtils.tla_fixer(result)
        self.assertEqual(fixed_result, "Approved for Patient J R T (JRT)")

    def test_note_remover(self):
        result = "This is a summary.\n* Note: This is additional information."
        cleaned_result = CleanerUtils.note_remover(result)
        self.assertEqual(cleaned_result, "This is a summary.")

    def test_remove_control_characters(self):
        result = "Clean this text\u0000 with control chars."
        cleaned_result = CleanerUtils.remove_control_characters(result)
        self.assertEqual(cleaned_result, "Clean this text with control chars.")

    def test_json_fix_missing_quotes(self):
        result = "{key1: value1, key2: value2}"
        fixed_json = CleanerUtils.json_fix_missing_quotes(result)
        self.assertEqual(fixed_json, '{"key1": value1, "key2": value2}')

    def test_json_fix_missing_colons(self):
        result = "{key1 value1, key2 value2}"
        fixed_json = CleanerUtils.json_fix_missing_colons(result)
        self.assertEqual(fixed_json, '{"key1": value1, "key2": value2}')

    def test_json_fix_missing_colons_noop_on_valid(self):
        result = """{"key1": "value1", "key2": "value2"}"""
        fixed_json = CleanerUtils.json_fix_missing_colons(result)
        self.assertEqual(fixed_json, '{"key1": "value1", "key2": "value2"}')

    def test_cleanup_json(self):
        incomplete_json = '{"key1": "value1", "key2": "value2",'
        cleaned_json = CleanerUtils.cleanup_json(incomplete_json)
        self.assertEqual(cleaned_json, {"key1": "value1", "key2": "value2"})

    def test_cleanup_lt(self):
        result = "Note that this is irrelevant information."
        cleaned_result = CleanerUtils.cleanup_lt("general", result)
        self.assertEqual(cleaned_result, "")

    def test_url_fixer(self):
        result = "Visit https://invalidurl.fake and https://validurl.com for details."
        fixed_result = CleanerUtils.url_fixer(result)
        self.assertNotIn("https://invalidurl.fake", fixed_result)

    def test_is_valid_url(self):
        self.assertTrue(CleanerUtils.is_valid_url("https://www.google.com"))
        self.assertFalse(CleanerUtils.is_valid_url("https://invalidurl.fake"))

if __name__ == "__main__":
    unittest.main()
