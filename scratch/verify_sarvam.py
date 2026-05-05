from __future__ import annotations
import unittest
from unittest.mock import MagicMock, patch
import json
from app.services.summarization import summarize_articles_batch
from app.core.config import get_settings

class TestSummarizationProviderSwitching(unittest.TestCase):
    def setUp(self):
        self.settings = get_settings()
        self.settings.openrouter_api_key = "fake-openrouter-key"
        self.settings.sarvam_ai_api_key = "fake-sarvam-key"

    @patch("app.services.summarization.OpenAI")
    def test_uses_openrouter_for_english(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
            "articles": [{"source_url": "http://test.com", "title": "EN Title", "content": "EN Summary", "category": "General"}]
        })))]
        mock_client.chat.completions.create.return_value = mock_response

        articles = [{"url": "http://test.com", "source_name": "Test", "original_title": "Old", "original_content": "Long content", "publish_date": "2024-01-01"}]
        results = summarize_articles_batch(articles, language="english")

        # Verify OpenRouter was called
        mock_openai_class.assert_called_with(base_url="https://openrouter.ai/api/v1", api_key="fake-openrouter-key")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "EN Title")

    @patch("app.services.summarization.SarvamAI")
    def test_uses_sarvam_for_odia(self, mock_sarvam_client_class):
        mock_client = MagicMock()
        mock_sarvam_client_class.return_value = mock_client
        
        # Mock successful Sarvam response (Object based)
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps({
            "articles": [{"source_url": "http://test.com", "title": "Odia Title", "content": "Odia Summary", "category": "General"}]
        })
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.return_value = mock_response

        articles = [{"url": "http://test.com", "source_name": "Test", "original_title": "Old", "original_content": "Long content", "publish_date": "2024-01-01"}]
        results = summarize_articles_batch(articles, language="odia")

        # Verify Sarvam AI SDK was called
        mock_sarvam_client_class.assert_called_with(api_subscription_key="fake-sarvam-key")
        mock_client.chat.completions.assert_called_once()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Odia Title")

    @patch("app.services.summarization._request_summary_sarvam")
    def test_sarvam_failure_uses_fallback(self, mock_sarvam_req):
        mock_sarvam_req.return_value = "" # Simulate failure

        articles = [{"url": "http://test.com", "source_name": "Test", "original_title": "Original Title", "original_content": "Original content", "publish_date": "2024-01-01"}]
        results = summarize_articles_batch(articles, language="bengali")

        # Verify fallback was used (Article title matches original)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Original Title")

if __name__ == "__main__":
    unittest.main()
