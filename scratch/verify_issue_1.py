from __future__ import annotations
import unittest
from unittest.mock import MagicMock, patch
from app.services.extractor import ArticleExtractor
from app.services.scraping_config import MAX_ARTICLES_PER_SOURCE
from app.core.config import BATCH_SIZE

class TestIssue1Verification(unittest.TestCase):
    def test_max_articles_per_source_value(self):
        # Verify that MAX_ARTICLES_PER_SOURCE is set to 5
        self.assertEqual(MAX_ARTICLES_PER_SOURCE, 5)

    def test_batch_size_value(self):
        # Verify that BATCH_SIZE is set to 5
        self.assertEqual(BATCH_SIZE, 5)

    @patch("app.services.extractor.feedparser.parse")
    def test_extract_articles_limit_logic(self, mock_parse):
        # Mock a feed with 10 entries
        mock_feed = MagicMock()
        mock_feed.entries = [MagicMock(link=f"https://example.com/{i}", title=f"Title {i}") for i in range(10)]
        mock_parse.return_value = mock_feed

        extractor = ArticleExtractor()
        
        # Mock _extract_single_article to succeed for all entries
        extractor._extract_single_article = MagicMock(side_effect=lambda entry, patterns, source: {
            "original_title": entry.title,
            "url": entry.link
        })

        # Test with limit of 3
        results = extractor.extract_articles("https://rss.url", [], "Test Source", max_articles=3)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["original_title"], "Title 0")
        self.assertEqual(results[2]["original_title"], "Title 2")

        # Test with limit of 7 (should stop at 7)
        results = extractor.extract_articles("https://rss.url", [], "Test Source", max_articles=7)
        self.assertEqual(len(results), 7)

    @patch("app.services.extractor.feedparser.parse")
    def test_extract_articles_skips_invalid_entries(self, mock_parse):
        # Mock a feed with 10 entries
        mock_feed = MagicMock()
        mock_feed.entries = [MagicMock(link=f"https://example.com/{i}", title=f"Title {i}") for i in range(10)]
        mock_parse.return_value = mock_feed

        extractor = ArticleExtractor()
        
        # Mock _extract_single_article to fail for even indices
        def fake_extract(entry, patterns, source):
            index = int(entry.link.split("/")[-1])
            if index % 2 == 0:
                return None
            return {"original_title": entry.title, "url": entry.link}
            
        extractor._extract_single_article = MagicMock(side_effect=fake_extract)

        # Test with limit of 3. Indices 1, 3, 5 should be returned.
        results = extractor.extract_articles("https://rss.url", [], "Test Source", max_articles=3)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["original_title"], "Title 1")
        self.assertEqual(results[1]["original_title"], "Title 3")
        self.assertEqual(results[2]["original_title"], "Title 5")

if __name__ == "__main__":
    unittest.main()
