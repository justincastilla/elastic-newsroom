"""
JSON extraction utilities for Elastic News

Provides robust JSON extraction from LLM responses, handling common issues like
markdown formatting, truncation, and malformed JSON.
"""

import json
import re
import logging
from typing import Dict, Any, Optional


def extract_json_from_llm_response(
    response_text: str,
    logger: Optional[logging.Logger] = None
) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON from an LLM response, handling common formatting issues.
    
    This function handles several common issues with LLM-generated JSON:
    - Markdown code blocks (```json ... ``` or ``` ... ```)
    - Extra text before/after the JSON object
    - Trailing commas before closing brackets/braces
    - Truncated JSON (attempts to close unclosed objects/arrays)
    
    Args:
        response_text: The raw text response from the LLM
        logger: Optional logger for debugging messages
        
    Returns:
        Parsed JSON as a dictionary, or None if parsing fails
        
    Example:
        >>> from utils import extract_json_from_llm_response, setup_logger
        >>> logger = setup_logger("MY_AGENT")
        >>> response = "```json\\n{\\\"key\\\": \\\"value\\\"}\\n```"
        >>> data = extract_json_from_llm_response(response, logger)
        >>> print(data)
        {'key': 'value'}
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Try to extract JSON if there's any markdown formatting
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Try to find JSON object boundaries if still contains extra text
        if not response_text.startswith("{"):
            # Find first { and last }
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                response_text = response_text[start_idx:end_idx + 1]
        
        # Attempt to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as json_err:
            logger.error(f"JSON parsing failed: {json_err}")
            logger.error(f"Full JSON response length: {len(response_text)} chars")
            logger.error(f"Problematic JSON text (first 1000 chars): {response_text[:1000]}")
            
            # Try to fix common JSON issues
            # 1. Remove trailing commas before closing brackets/braces
            response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
            
            # 2. Fix missing commas between array elements
            # Look for patterns like "}" followed by "{" which should have a comma
            response_text = re.sub(r'}\s*{', '},{', response_text)
            
            # 3. Fix missing commas between object properties
            # Look for patterns like '"}' followed by '"' which should have a comma
            response_text = re.sub(r'"}\s*"', '"},"', response_text)
            
            # 4. Fix missing commas in arrays of objects
            # Look for patterns like "}" followed by "]" which should have a comma
            response_text = re.sub(r'}\s*]', '},]', response_text)
            
            # 5. Fix missing commas between array elements (more specific)
            # Look for "}" followed by whitespace and "{" in arrays
            response_text = re.sub(r'}\s*{\s*"', '},{"', response_text)
            
            # 2. Check if JSON is truncated - if it doesn't end with }, try to close it
            response_text = response_text.strip()
            if not response_text.endswith('}'):
                logger.warning(f"JSON appears truncated, ends with: {response_text[-50:]}")
                # Count open braces and brackets
                open_braces = response_text.count('{') - response_text.count('}')
                open_brackets = response_text.count('[') - response_text.count(']')
                
                # Try to close them
                logger.info(f"Attempting to close: {open_brackets} unclosed arrays, {open_braces} unclosed objects")
                response_text += ']' * open_brackets
                response_text += '}' * open_braces
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as repair_err:
                logger.error(f"Failed to repair JSON: {repair_err}")
                logger.error(f"Final attempted JSON (first 1000 chars): {response_text[:1000]}")
                return None
                
    except Exception as e:
        logger.error(f"Unexpected error during JSON extraction: {e}")
        return None
