# SDR Transcription Workflow

A comprehensive system for downloading, transcribing, and summarizing Software Defined Radio (SDR) recordings from a remote Raspberry Pi.

## Overview

This project automates the process of:
1. Downloading WAV recordings from a remote Raspberry Pi hosting an SDR setup
2. Transcribing audio recordings using OpenAI's Whisper speech-to-text model
3. Analyzing and summarizing the transcripts using Anthropic's Claude AI
4. Organizing all files into a structured workflow

The system is particularly optimized for police dispatch radio transcription and analysis.

## Key Components

- **SDR Workflow Runner** (`run_daily_transfer_and_summary.sh`): Bash script that sets up the environment and runs the workflow
- **Main Controller** (`main.py`): Entry point that parses command-line arguments and configures the workflow
- **Workflow Engine** (`workflow.py`): Core workflow class that handles the end-to-end process
- **Claude Integration** (`claude_handler.py`): Handles API communication with Anthropic's Claude
- **Logging System** (`logger.py`): Custom logging implementation for tracking operations

## Requirements

- Python 3.7+
- SSH key access to remote Raspberry Pi
- Anthropic Claude API key (starts with `sk-ant-`)
- Dependencies:
  - paramiko (SSH/SFTP client)
  - torch
  - OpenAI Whisper
  - requests
  - numpy
  - setuptools-rust

## Setup

1. Clone this repository:
   ```
   git clone <repository-url>
   cd sdr_workflow
   ```

2. Ensure SSH key access to your Raspberry Pi.

3. Set your env file up:
```
CLAUDE_API_KEY=sk-ant-XXXXXXX
HOST=SOME_HOST
USERNAME=REMOTE_USERNAME
KEY_PATH=SSH_KEYPATH
REMOTE_DIR=REMOTE_HOST_AUDIO_FILE_DIR
```
4. Make the runner script executable:
   ```
   chmod +x run_daily_transfer_and_summary.sh
   ```

## Directory Structure

The system creates and uses the following directory structure:

```
~/sdr_workflow/
├── logs/          # Log files
├── recordings/    # Downloaded WAV files
├── transcripts/   # Transcription results (TXT and JSON)
├── daily_summaries/ # Summarized reports
└── venv/          # Python virtual environment
```

## Usage

### Basic Usage

Run the workflow with default settings:

```bash
./run_daily_transfer_and_summary.sh
```

### Advanced Usage

Run with custom options:

```bash
python main.py --cleanup --claude-model=claude-3-opus-20240229 --max-tokens=500 --temperature=0.5
```

### Command-Line Options

- `--cleanup`: Delete WAV files from Raspberry Pi after downloading
- `--claude-api-key=KEY`: Specify Claude API key directly
- `--claude-model=MODEL`: Choose Claude model (default: claude-3-7-sonnet-20250219)
- `--max-tokens=N`: Maximum tokens for summary generation (default: 300)
- `--temperature=N`: Temperature for generation (default: 0.7)
- `--log-level=LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Configuration

Add .env file with your API key and remote host details

Default configuration is defined in `main.py`:

```python
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
```

## Automation

Set up a cron job to run the workflow daily:

```
# Run the SDR workflow daily at 6 AM
0 6 * * * /path/to/run_daily_transfer_and_summary.sh
```

## Logging

The system generates detailed logs in two locations:
- Runner script logs: `~/sdr_workflow/logs/runner_YYYYMMDD_HHMMSS.log`
- Python workflow logs: `~/sdr_workflow/logs/sdr_workflow_YYYYMMDD_HHMMSS.log`

## Transcription Format

The transcribed audio is saved with timestamps in the format:
```
[MM:SS.mmm --> MM:SS.mmm] Transcribed text
```

## Summary Generation

The Claude AI is prompted to analyze the transcripts specifically for police dispatch communications, identifying:
- Distinct calls or incidents based on time gaps and unit identifiers
- Time ranges for each incident
- Units involved
- Nature of calls
- Key details and resolutions

## Troubleshooting

- **SSH Connection Issues**: Verify SSH key path and permissions
- **Missing WAV Files**: Check the remote directory path and file permissions
- **Whisper Model Errors**: Ensure adequate disk space and RAM for model loading
- **Claude API Errors**: Verify API key format and validity (should start with 'sk-ant-')

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Anthropic Claude](https://www.anthropic.com/claude) for transcript analysis
- [Paramiko](https://www.paramiko.org/) for SSH/SFTP functionality