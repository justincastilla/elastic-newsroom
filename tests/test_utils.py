#!/usr/bin/env python3
"""
Unit Tests for Utility Functions

Tests the utility functions in the utils module to ensure
they work correctly and handle edge cases.
"""

import os
import json
import logging
import tempfile
from unittest.mock import patch, MagicMock
import pytest

# Import utility functions
from utils import (
    load_env_config,
    init_anthropic_client,
    extract_json_from_llm_response,
    setup_logger
)


class TestEnvLoader:
    """Tests for environment variable loading"""
    
    def test_load_env_config_basic(self):
        """Test that load_env_config runs without errors"""
        # Should not raise any exceptions
        load_env_config()
        assert True  # If we get here, it didn't crash


class TestAnthropicClient:
    """Tests for Anthropic client initialization"""
    
    def test_init_anthropic_client_with_key(self):
        """Test Anthropic client initialization with API key"""
        logger = setup_logger("TEST")
        
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("utils.anthropic_client.Anthropic") as mock_anthropic:
                client = init_anthropic_client(logger)
                assert client is not None
                mock_anthropic.assert_called_once_with(api_key="test-key")
    
    def test_init_anthropic_client_without_key(self):
        """Test Anthropic client initialization without API key"""
        logger = setup_logger("TEST")
        
        with patch.dict(os.environ, {}, clear=True):
            client = init_anthropic_client(logger)
            assert client is None


class TestJsonExtraction:
    """Tests for JSON extraction from LLM responses"""
    
    def test_extract_clean_json(self):
        """Test extraction of clean JSON"""
        logger = setup_logger("TEST")
        response = '{"key": "value", "number": 42}'
        
        result = extract_json_from_llm_response(response, logger)
        assert result is not None
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_extract_json_with_markdown(self):
        """Test extraction of JSON wrapped in markdown code blocks"""
        logger = setup_logger("TEST")
        response = '''```json
{
  "key": "value",
  "number": 42
}
```'''
        
        result = extract_json_from_llm_response(response, logger)
        assert result is not None
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_extract_json_with_generic_markdown(self):
        """Test extraction of JSON wrapped in generic code blocks"""
        logger = setup_logger("TEST")
        response = '''```
{
  "key": "value",
  "number": 42
}
```'''
        
        result = extract_json_from_llm_response(response, logger)
        assert result is not None
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_extract_json_with_extra_text(self):
        """Test extraction of JSON with extra text before/after"""
        logger = setup_logger("TEST")
        response = 'Here is your JSON: {"key": "value", "number": 42} and some extra text'
        
        result = extract_json_from_llm_response(response, logger)
        assert result is not None
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_extract_json_with_trailing_comma(self):
        """Test extraction of JSON with trailing comma (common LLM error)"""
        logger = setup_logger("TEST")
        response = '{"key": "value", "array": [1, 2, 3,],}'
        
        result = extract_json_from_llm_response(response, logger)
        assert result is not None
        assert result["key"] == "value"
        assert result["array"] == [1, 2, 3]
    
    def test_extract_truncated_json(self):
        """Test extraction of truncated JSON (missing closing braces)"""
        logger = setup_logger("TEST")
        response = '{"key": "value", "nested": {"inner": "data"'
        
        result = extract_json_from_llm_response(response, logger)
        # Should attempt to fix by closing braces
        assert result is not None
        assert result["key"] == "value"
        assert "nested" in result
    
    def test_extract_invalid_json(self):
        """Test extraction of completely invalid JSON"""
        logger = setup_logger("TEST")
        response = 'This is not JSON at all, just plain text!'
        
        result = extract_json_from_llm_response(response, logger)
        assert result is None


class TestLogger:
    """Tests for logger setup"""
    
    def test_setup_logger_basic(self):
        """Test basic logger setup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logger("TEST", log_file=log_file)
            
            assert logger is not None
            assert logger.name == "TEST"
            assert logger.level == logging.INFO
            
            # Test logging works
            logger.info("Test message")
            
            # Verify log file was created
            assert os.path.exists(log_file)


def run_tests():
    """Run all tests"""
    print("🧪 Running Utility Function Tests")
    print("=" * 60)
    
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
