#!/bin/bash
set -e

# Check if env file was provided
if [ -z "$1" ]; then
    echo "Error: No environment file provided"
    echo "Usage: docker run -v /path/to/data:/app/data -v /path/to/ssh-key:/app/ssh-key -v /path/to/.env:/app/.env your-image /app/.env"
    exit 1
fi

ENV_FILE="$1"

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file '$ENV_FILE' not found"
    exit 1
fi

# Load environment variables from file
set -a
source "$ENV_FILE"
set +a

# Ensure SSH key has proper permissions
if [ ! -z "$KEY_PATH" ] && [ -f "$KEY_PATH" ]; then
    chmod 600 "$KEY_PATH"
fi

# Ensure data directories exist
mkdir -p /app/data/logs
mkdir -p /app/data/recordings
mkdir -p /app/data/transcripts
mkdir -p /app/data/daily_summaries
mkdir -p /app/data/venv

# Run the main application
python main.py \
    --claude-api-key="${CLAUDE_API_KEY}" \
    --host="${HOST}" \
    --username="${USERNAME}" \
    --key_path="${KEY_PATH}" \
    --remote_dir="${REMOTE_DIR}" \
    --cleanup \
    "$@"