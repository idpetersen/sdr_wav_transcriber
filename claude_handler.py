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
            max_transcript_length = 100000
            if len(transcript) > max_transcript_length:
                self.logger.warning(f"Truncating transcript from {len(transcript)} to {max_transcript_length} characters")
                transcript = transcript[:max_transcript_length]

            # Construct the system prompt
            system_prompt = """
Analyze this police dispatch transcript from [Department Name]. Identify and detail all incidents.
Format each incident with:
- Time range
- Units involved
- Nature of call
- Details
- Resolution (if any)
Department terminology:
- RP = Reporting Party
- Victor units = patrol units
- [Add any specific codes/terms for your department]
Include ALL communications and preserve all technical details."""

            # Construct request payload
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user", 
                        "content": transcript
                    }
                ],
                "system": system_prompt,
                "max_tokens": self.max_tokens
            }
            
            # Add temperature only if it's not the default (0.7)
            if self.temperature != 0.7:
                payload["temperature"] = self.temperature
            
            # Set up headers with the latest anthropic-version
            headers = {
                "content-type": "application/json",
                "x-api-key": f"{self.api_key}",
                "anthropic-version": "2023-06-01",
            }
            
            self.logger.debug(f"Making API request to Claude with {len(transcript)} characters of transcript")
            self.logger.debug(f"Headers passed: {headers}")
            self.logger.debug(f"Payload structure: {json.dumps(payload, indent=2)[:1000]}...")
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            # Check response
            if response.status_code != 200:
                self.logger.error(f"API Error: Status {response.status_code}")
                self.logger.error(f"Response body: {response.text}")
                return None
                
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
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            self.logger.error(f"Summary generation error: {e}")
            self.logger.debug(traceback.format_exc())
            return None