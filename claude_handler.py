#!/usr/bin/env python3
import requests
import json
import traceback
from pathlib import Path

class ClaudeHandler:
    """
    Handler for Anthropic Claude API operations to generate summaries from transcripts.
    """
    def __init__(self, logger, base_dir, api_key, 
                 model='claude-3-7-sonnet-20250219', max_tokens=300, temperature=0.7):
        """
        Initialize the Claude API handler with configuration.
        
        :param logger: Logger instance
        :param base_dir: Base directory for temporary files
        :param api_key: Anthropic API key
        :param model: Claude model to use
        :param max_tokens: Maximum tokens for generation
        :param temperature: Temperature for generation
        """
        self.logger = logger
        self.base_dir = Path(base_dir)
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api_url = "https://api.anthropic.com/v1/messages"
        
        # Validate API key format
        if not self.api_key or not self.api_key.startswith('sk-ant-'):
            self.logger.warning("Claude API key appears to be invalid (should start with 'sk-ant-')")
        else:
            self.logger.info("Claude API handler initialized")
    
    def generate_summary(self, transcript):
        """
        Generate summary using Claude API.
        
        :param transcript: Text to summarize
        :return: Generated summary or None
        """
        try:
            self.logger.info(f"Generating summary using Claude model: {self.model}")
            
            # Truncate very long transcripts to prevent API issues
            max_transcript_length = 100000  # Claude can handle much longer context than Ollama
            if len(transcript) > max_transcript_length:
                self.logger.warning(f"Truncating transcript from {len(transcript)} to {max_transcript_length} characters")
                transcript = transcript[:max_transcript_length]

            # Construct the system prompt
            system_prompt = """You are a police dispatch analyst who specializes in summarizing radio communications, identifying separate incidents, and providing clear summaries of police activities.
    Analyze and summarize the following police dispatch transcript.
    The transcript is formatted with timestamps [MM:SS.mmm --> MM:SS.mmm] followed by radio communications.
    Pay attention to the \\n characters as that denotes a new line
    IMPORTANT ANALYSIS GUIDELINES:
    1. Group communications into distinct "calls" or "incidents" based on:
    - Time gaps between transmissions (significant gaps often indicate different calls)
    - Continuity of unit identifiers (e.g., "Victor 4-7" indicates a specific unit)
    - References to the same incident, location, or situation
    2. For each identified call/incident, provide:
    - Time range (start and end timestamps)
    - Units involved (e.g., Victor numbers, other identifiers)
    - Nature of the call (if discernible)
    - Key details or developments
    - Resolution (if available)
    3. Use police/dispatch terminology appropriately in your summary
    - "RP" = Reporting Party
    - "Victor" units = patrol units
    - Code numbers may refer to specific types of calls"""

            # Construct request payload - fixing format to match API requirements
            payload = {
                "model": self.model,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": transcript}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            # Set up headers
            headers = {
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "x-api-key": self.api_key
            }
            
            self.logger.debug(f"Making API request to Claude with {len(transcript)} characters of transcript")
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            # Check response
            response.raise_for_status()
            response_data = response.json()
            
            # Extract summary from response
            if "content" in response_data and len(response_data["content"]) > 0:
                summary = response_data["content"][0]["text"]
                self.logger.info(f"Summary generated. Length: {len(summary)} characters")
                return summary
            else:
                self.logger.error(f"Unexpected API response structure: {json.dumps(response_data)[:500]}")
                return None
        
        except requests.RequestException as e:
            self.logger.error(f"Claude API request error: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.debug(f"Response status: {e.response.status_code}")
                self.logger.debug(f"Response body: {e.response.text[:500]}")
            return None
        except Exception as e:
            self.logger.error(f"Summary generation error: {e}")
            self.logger.debug(traceback.format_exc())
            return None