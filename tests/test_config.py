import unittest
from agent.config import settings

class TestConfig(unittest.TestCase):
    def test_settings_initialization(self):
        self.assertTrue(hasattr(settings, "OPENAI_API_KEY"))
        self.assertTrue(hasattr(settings, "NEWS_API_KEY"))
        self.assertTrue(hasattr(settings, "USER_AGENT"))
        self.assertTrue(len(settings.USER_AGENT) > 0)

if __name__ == "__main__":
    unittest.main()

