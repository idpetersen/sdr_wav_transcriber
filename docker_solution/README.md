# SDR Transcription Workflow Docker Container

This Docker implementation containerizes the SDR Transcription Workflow for easy deployment and consistent operation across environments.

## Features

- Containerized application with all dependencies included
- Proper volume mounting for persistent data
- Environment handling through .env files
- SSH key management for remote connections
- Configurable via Docker Compose or direct Docker commands

## Prerequisites

- Docker and Docker Compose installed
- SSH key for remote Raspberry Pi access
- Anthropic Claude API key

## Quick Start

1. Clone this repository:
   ```
   git clone https://github.com/idpetersen/sdr_wav_transcriber
   cd sdr_workflow/docker_solution
   ```

2. Create a `.env` file with the required environment variables:
   ```
   CLAUDE_API_KEY=sk-ant-XXXXXXX
   HOST=SOME_HOST
   USERNAME=REMOTE_USERNAME
   KEY_PATH=/app/ssh-key/id_rsa
   REMOTE_DIR=REMOTE_HOST_AUDIO_FILE_DIR
   ```

3. Build and run the container with Docker Compose:
   ```
   docker-compose up -d
   ```

## Manual Docker Setup

If you prefer to run without Docker Compose:

1. Build the Docker image:
   ```
   docker build -t sdr-workflow .
   ```

2. Create data directories:
   ```
   mkdir -p ./data/logs ./data/recordings ./data/transcripts ./data/daily_summaries
   ```

3. Run the container:
   ```
   docker run -v $(pwd)/data:/app/data \
     -v /path/to/ssh-key:/app/ssh-key \
     -v $(pwd)/.env:/app/.env \
     sdr-workflow /app/.env
   ```

## Volume Mounts

The container uses the following volume mounts:

- `./data:/app/data` - For all persistent data (recordings, transcripts, logs, etc.)
- `${SSH_KEY_PATH}:${SSH_KEY_PATH}` - SSH key for remote access
- `./.env:/app/.env` - Environment variables file

## Directory Structure

Inside the container, the following directory structure is used:

```
/app/
├── data/
│   ├── logs/
│   ├── recordings/
│   ├── transcripts/
│   └── daily_summaries/
├── ssh-key/
│   └── id_rsa  (your SSH private key)
└── .env
```

## Environment Variables

Required variables in the `.env` file:

- `CLAUDE_API_KEY`: Anthropic API key (starts with sk-ant-)
- `HOST`: Remote host (Raspberry Pi) address
- `USERNAME`: Remote host username
- `KEY_PATH`: Path to SSH private key (inside container)
- `REMOTE_DIR`: Directory on remote host containing WAV files

Optional variables:

- `BASE_DIR`: Base directory for all data (default: /app/data)

## Scheduled Operation

To run the container on a schedule:

1. Add a cron job on the host system:
   ```
   # Run daily at 6 AM
   0 6 * * * docker-compose -f /path/to/docker-compose.yml up
   ```

2. Or use a Docker scheduling solution like Ofelia.

## Troubleshooting

- **Permission Issues**: Ensure SSH key has proper permissions (600)
- **Volume Mount Problems**: Verify paths are absolute in docker-compose.yml
- **Connection Errors**: Check if host is reachable from container
- **Missing Data**: Confirm volume mount points are correct