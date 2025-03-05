#!/usr/bin/env python3
import os
import argparse
import logging

from workflow import SDRTranscriptionWorkflow

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='SDR Transcription Workflow')
    parser.add_argument('--cleanup', 
                        action='store_true', 
                        help='Clean up remote recordings directory after download')
    
    # Add Claude-specific arguments
    parser.add_argument('--claude-api-key',
                        default=os.environ.get('CLAUDE_API_KEY', ''),
                        help='Anthropic Claude API key (or set CLAUDE_API_KEY env var)')
    parser.add_argument('--claude-model',
                        default='claude-3-7-sonnet-20250219',
                        help='Claude model to use (default: claude-3-7-sonnet-20250219)')
    parser.add_argument('--host',
                        default=os.environ.get('HOST', ''),
                        help='IP or Hostname of remote host')
    parser.add_argument('--username',
                        default=os.environ.get('USERNAME', ''),
                        help='Username of user on remote host')
    parser.add_argument('--key_path',
                        default=os.environ.get('KEY_PATH', ''),
                        help='Key path to SSH key for remote host')
    parser.add_argument('--remote_dir',
                        default=os.environ.get('REMOTE_DIR', ''),
                        help='Dir where WAV/MP3 files are on remote host')
    parser.add_argument('--max-tokens',
                        type=int,
                        default=5000,
                        help='Maximum tokens for summary generation (default: 5000)')
    parser.add_argument('--temperature',
                        type=float,
                        default=0.7,
                        help='Temperature for generation (default: 0.7)')
    parser.add_argument('--log-level',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO',
                        help='Set logging level (default: INFO)')

    args = parser.parse_args()

    # Convert log level string to logging constant
    log_level = getattr(logging, args.log_level)

    # Configuration dictionary
    config = {
        'host': args.host,
        'username': args.username,
        'key_path': args.key_path,
        'remote_dir': args.remote_dir,
        'base_dir': os.path.expanduser('~/sdr_workflow'),
        'log_dir': os.path.expanduser('~/sdr_workflow/logs'),
        'whisper_model': 'medium.en',
        'claude_api_key': args.claude_api_key,
        'claude_model': args.claude_model,
        'max_tokens': args.max_tokens,
        'temperature': args.temperature
    }

    # Create and run workflow with specified log level
    workflow = SDRTranscriptionWorkflow(config, cleanup=args.cleanup, log_level=log_level)
    workflow.run_workflow()

if __name__ == '__main__':
    main()