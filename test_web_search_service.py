#!/usr/bin/env python3
"""
Unit tests for the Web Search Service.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
from web_search_service import WebSearchService, SearchResult, get_search_service, reset_search_service


class TestSearchResult(unittest.TestCase):
    """Test the SearchResult class."""
    
    def test_search_result_creation(self):
        """Test creating a SearchResult object."""
        result = SearchResult(
            title="Test Title",
            snippet="Test snippet content",
            url="https://example.com",
            position=0
        )
        
        self.assertEqual(result.title, "Test Title")
        self.assertEqual(result.snippet, "Test snippet content")
        self.assertEqual(result.url, "https://example.com")
        self.assertEqual(result.position, 0)
        self.assertEqual(result.relevance_score, 1.0)
    
    def test_search_result_relevance_score(self):
        """Test relevance score calculation based on position."""
        result1 = SearchResult("Title", "Snippet", "URL", position=0)
        result2 = SearchResult("Title", "Snippet", "URL", position=1)
        result3 = SearchResult("Title", "Snippet", "URL", position=4)
        
        self.assertEqual(result1.relevance_score, 1.0)
        self.assertEqual(result2.relevance_score, 0.5)
        self.assertEqual(result3.relevance_score, 0.2)
    
    def test_search_result_to_dict(self):
        """Test converting SearchResult to dictionary."""
        result = SearchResult(
            title="Test Title",
            snippet="Test snippet",
            url="https://example.com",
            position=2
        )
        
        result_dict = result.to_dict()
        self.assertEqual(result_dict["title"], "Test Title")
        self.assertEqual(result_dict["snippet"], "Test snippet")
        self.assertEqual(result_dict["url"], "https://example.com")
        self.assertEqual(result_dict["position"], 2)
        self.assertAlmostEqual(result_dict["relevance_score"], 1/3)


class TestWebSearchService(unittest.TestCase):
    """Test the WebSearchService class."""
    
    def setUp(self):
        """Set up test environment."""
        # Save original environment variables
        self.orig_env = os.environ.copy()
        # Reset singleton
        reset_search_service()
    
    def tearDown(self):
        """Clean up test environment."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.orig_env)
        # Reset singleton
        reset_search_service()
    
    @patch.dict('os.environ', {'SERPAPI_API_KEY': 'test-key', 'WEB_SEARCH_ENABLED': 'true'})
    def test_service_initialization_enabled(self):
        """Test service initialization when enabled."""
        service = WebSearchService()
        
        self.assertTrue(service.is_enabled())
        self.assertEqual(service.api_key, 'test-key')
        self.assertEqual(service.max_results, 5)
    
    @patch.dict('os.environ', {'WEB_SEARCH_ENABLED': 'false', 'SERPAPI_API_KEY': 'test-key'})
    def test_service_initialization_disabled(self):
        """Test service initialization when disabled by config."""
        service = WebSearchService()
        
        self.assertFalse(service.is_enabled())
    
    @patch.dict('os.environ', {'WEB_SEARCH_ENABLED': 'true'})
    def test_service_initialization_no_api_key(self):
        """Test service initialization without API key."""
        # Remove SERPAPI_API_KEY if it exists
        os.environ.pop('SERPAPI_API_KEY', None)
        
        service = WebSearchService()
        
        self.assertFalse(service.is_enabled())
    
    def test_service_custom_initialization(self):
        """Test service initialization with custom parameters."""
        service = WebSearchService(
            api_key="custom-key",
            max_results=10,
            enabled=True
        )
        
        self.assertEqual(service.api_key, "custom-key")
        self.assertEqual(service.max_results, 10)
        # Will be disabled if GoogleSearch is not available
        if service.enabled:
            self.assertTrue(service.is_enabled())
    
    @patch('web_search_service.GoogleSearch')
    @patch.dict('os.environ', {'SERPAPI_API_KEY': 'test-key', 'WEB_SEARCH_ENABLED': 'true'})
    def test_search_general(self, mock_google_search):
        """Test general search functionality."""
        # Mock search results
        mock_search_instance = Mock()
        mock_search_instance.get_dict.return_value = {
            "organic_results": [
                {
                    "title": "Result 1",
                    "snippet": "Snippet 1",
                    "link": "https://example1.com"
                },
                {
                    "title": "Result 2",
                    "snippet": "Snippet 2",
                    "link": "https://example2.com"
                }
            ]
        }
        mock_google_search.return_value = mock_search_instance
        
        service = WebSearchService()
        results = service.search("test query")
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].title, "Result 1")
        self.assertEqual(results[0].snippet, "Snippet 1")
        self.assertEqual(results[0].url, "https://example1.com")
        self.assertEqual(results[0].position, 0)
    
    @patch('web_search_service.GoogleSearch')
    @patch.dict('os.environ', {'SERPAPI_API_KEY': 'test-key', 'WEB_SEARCH_ENABLED': 'true'})
    def test_search_with_type(self, mock_google_search):
        """Test search with different search types."""
        mock_search_instance = Mock()
        mock_search_instance.get_dict.return_value = {"organic_results": []}
        mock_google_search.return_value = mock_search_instance
        
        service = WebSearchService()
        
        # Test technical search
        service.search("test query", search_type="technical")
        call_args = mock_google_search.call_args[0][0]
        self.assertIn("technical documentation implementation", call_args["q"])
        
        # Test standards search
        service.search("test query", search_type="standards")
        call_args = mock_google_search.call_args[0][0]
        self.assertIn("standard specification RFC", call_args["q"])
    
    @patch.dict('os.environ', {'WEB_SEARCH_ENABLED': 'false'})
    def test_search_when_disabled(self):
        """Test search returns empty list when disabled."""
        service = WebSearchService()
        results = service.search("test query")
        
        self.assertEqual(results, [])
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        service = WebSearchService(api_key="test", enabled=True)
        
        results = service.search("")
        self.assertEqual(results, [])
        
        results = service.search("   ")
        self.assertEqual(results, [])
    
    @patch('web_search_service.GoogleSearch')
    @patch.dict('os.environ', {'SERPAPI_API_KEY': 'test-key', 'WEB_SEARCH_ENABLED': 'true'})
    def test_search_error_handling(self, mock_google_search):
        """Test search error handling."""
        mock_google_search.side_effect = Exception("API Error")
        
        service = WebSearchService()
        results = service.search("test query")
        
        self.assertEqual(results, [])
    
    @patch('web_search_service.GoogleSearch')
    @patch.dict('os.environ', {'SERPAPI_API_KEY': 'test-key', 'WEB_SEARCH_ENABLED': 'true'})
    def test_search_similar_standards(self, mock_google_search):
        """Test searching for similar standards."""
        mock_search_instance = Mock()
        mock_search_instance.get_dict.return_value = {
            "organic_results": [
                {
                    "title": "OAuth 2.0 Standard",
                    "snippet": "The OAuth 2.0 authorization framework",
                    "link": "https://oauth.net/2/"
                }
            ]
        }
        mock_google_search.return_value = mock_search_instance
        
        service = WebSearchService()
        results = service.search_similar_standards(
            "OAuth JWT security",
            ["Authentication", "Authorization"]
        )
        
        self.assertEqual(len(results), 1)
        call_args = mock_google_search.call_args[0][0]
        self.assertIn("OAuth JWT security", call_args["q"])
        self.assertIn("standards", call_args["q"])
        self.assertIn("Authentication", call_args["q"])
    
    @patch('web_search_service.GoogleSearch')
    @patch.dict('os.environ', {'SERPAPI_API_KEY': 'test-key', 'WEB_SEARCH_ENABLED': 'true'})
    def test_search_references(self, mock_google_search):
        """Test searching for references."""
        mock_search_instance = Mock()
        mock_search_instance.get_dict.return_value = {
            "organic_results": [
                {
                    "title": "Security Best Practices",
                    "snippet": "Implementation guide for security",
                    "link": "https://example.com/security"
                }
            ]
        }
        mock_google_search.return_value = mock_search_instance
        
        service = WebSearchService()
        results = service.search_references(
            "Authentication Guidelines",
            "OAuth security implementation"
        )
        
        self.assertEqual(len(results), 1)
        call_args = mock_google_search.call_args[0][0]
        self.assertIn("Authentication Guidelines", call_args["q"])
        self.assertIn("OAuth security implementation", call_args["q"])
        self.assertIn("examples implementation guide", call_args["q"])
    
    @patch('web_search_service.GoogleSearch')
    @patch.dict('os.environ', {'SERPAPI_API_KEY': 'test-key', 'WEB_SEARCH_ENABLED': 'true'})
    def test_search_document_templates(self, mock_google_search):
        """Test searching for document templates."""
        mock_search_instance = Mock()
        mock_search_instance.get_dict.return_value = {
            "organic_results": [
                {
                    "title": "Technical Standard Template",
                    "snippet": "Template for technical standards",
                    "link": "https://example.com/template"
                }
            ]
        }
        mock_google_search.return_value = mock_search_instance
        
        service = WebSearchService()
        results = service.search_document_templates(
            "Technical Standard",
            "security"
        )
        
        self.assertEqual(len(results), 1)
        call_args = mock_google_search.call_args[0][0]
        self.assertIn("Technical Standard", call_args["q"])
        self.assertIn("template", call_args["q"])
        self.assertIn("security", call_args["q"])
    
    @patch('web_search_service.GoogleSearch')
    @patch.dict('os.environ', {'SERPAPI_API_KEY': 'test-key', 'WEB_SEARCH_ENABLED': 'true'})
    def test_verify_references(self, mock_google_search):
        """Test reference verification."""
        # First reference found
        mock_search_instance1 = Mock()
        mock_search_instance1.get_dict.return_value = {
            "organic_results": [
                {
                    "title": "OAuth 2.0 RFC",
                    "snippet": "The OAuth 2.0 authorization framework",
                    "link": "https://tools.ietf.org/html/rfc6749"
                }
            ]
        }
        
        # Second reference not found
        mock_search_instance2 = Mock()
        mock_search_instance2.get_dict.return_value = {
            "organic_results": []
        }
        
        mock_google_search.side_effect = [mock_search_instance1, mock_search_instance2]
        
        service = WebSearchService()
        results = service.verify_references([
            "OAuth 2.0",
            "Nonexistent Standard XYZ"
        ])
        
        self.assertTrue(results["OAuth 2.0"])
        self.assertFalse(results["Nonexistent Standard XYZ"])
    
    def test_get_config(self):
        """Test getting service configuration."""
        service = WebSearchService(
            api_key="test-key",
            max_results=10,
            enabled=True
        )
        
        config = service.get_config()
        self.assertIn("enabled", config)
        self.assertIn("max_results", config)
        self.assertIn("api_key_present", config)
        self.assertEqual(config["max_results"], 10)
        self.assertTrue(config["api_key_present"])


class TestSingletonPattern(unittest.TestCase):
    """Test the singleton pattern for default service instance."""
    
    def setUp(self):
        """Reset singleton before each test."""
        reset_search_service()
    
    def tearDown(self):
        """Reset singleton after each test."""
        reset_search_service()
    
    @patch.dict('os.environ', {'SERPAPI_API_KEY': 'test-key', 'WEB_SEARCH_ENABLED': 'true'})
    def test_get_search_service_singleton(self):
        """Test that get_search_service returns the same instance."""
        service1 = get_search_service()
        service2 = get_search_service()
        
        self.assertIs(service1, service2)
    
    def test_reset_search_service(self):
        """Test resetting the search service."""
        service1 = get_search_service()
        reset_search_service()
        service2 = get_search_service()
        
        self.assertIsNot(service1, service2)


if __name__ == "__main__":
    unittest.main()