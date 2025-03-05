#!/bin/bash
# SDR Workflow Runner Script
# This script sets up a Python virtual environment, runs the SDR transcription workflow,
# and cleans up afterward. Designed to be run via cron.

# Exit on any error
set -e

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="${HOME}/sdr_workflow"
VENV_DIR="${BASE_DIR}/venv"
LOG_DIR="${BASE_DIR}/logs"
SCRIPT_PATH="${SCRIPT_DIR}/main.py"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/runner_${TIMESTAMP}.log"
API_KEY_DIR="$(pwd)"

if [ -f "${API_KEY_DIR}/.env"  ]; then
    set -a; source "${API_KEY_DIR}/.env"; set +a
else
  echo ".env file not found in current directory"
  exit 1
fi

# Ensure base directories exist
mkdir -p "${BASE_DIR}"
mkdir -p "${LOG_DIR}"

# Function for logging
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "${message}" | tee -a "${LOG_FILE}"
}

# Function for error handling
handle_error() {
    log "ERROR: An error occurred at line $1"
    log "Script execution failed"
    # Deactivate virtual environment if active
    if [[ -n "${VIRTUAL_ENV}" ]]; then
        log "Deactivating virtual environment due to error"
        deactivate
    fi
    exit 1
}

# Set up error trap
trap 'handle_error $LINENO' ERR

# Start logging
log "Starting SDR Workflow Runner"

# Check if Python script exists
if [ ! -f "${SCRIPT_PATH}" ]; then
    log "ERROR: Python script not found at ${SCRIPT_PATH}"
    exit 1
fi

# Setup virtual environment
if [ ! -d "${VENV_DIR}" ]; then
    log "Creating virtual environment at ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
    if [ $? -ne 0 ]; then
        log "ERROR: Failed to create virtual environment"
        exit 1
    fi
else
    log "Using existing virtual environment at ${VENV_DIR}"
fi

# Activate virtual environment
log "Activating virtual environment"
source "${VENV_DIR}/bin/activate"
if [ $? -ne 0 ]; then
    log "ERROR: Failed to activate virtual environment"
    exit 1
fi

# Install or update dependencies
log "Installing/updating required packages"
pip install --upgrade pip 2>&1 | tee -a "${LOG_FILE}"
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    log "ERROR: Failed to upgrade pip"
    deactivate
    exit 1
fi

log "Installing required packages (this may take a few minutes)..."
pip install paramiko torch requests numpy 2>&1 --quiet | tee -a "${LOG_FILE}" 
pip install git+https://github.com/openai/whisper.git --quiet | tee -a "${LOG_FILE}" 
pip install --upgrade --no-deps --force-reinstall git+https://github.com/openai/whisper.git --quiet | tee -a "${LOG_FILE}" 
pip install setuptools-rust --quiet | tee -a "${LOG_FILE}" 

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    log "ERROR: Failed to install required packages"
    deactivate
    exit 1
fi

# Check for Claude API key
if [ -z "${CLAUDE_API_KEY}" ]; then
    log "WARNING: CLAUDE_API_KEY not found in environment or ~/.claude_api_key file"
    log "You will need to provide the API key as a command line argument"
fi

# Run the Python script with output redirected to both console and log file
log "Running SDR transcription workflow script"
log "----------------------------------------"
python "${SCRIPT_PATH}" --claude-api-key="${CLAUDE_API_KEY}" --host="${HOST}" --username="${USERNAME}" --key_path="${KEY_PATH}" --remote_dir="${REMOTE_DIR}" --cleanup 2>&1 | tee -a "${LOG_FILE}"
PYTHON_EXIT_CODE=${PIPESTATUS[0]}
log "----------------------------------------"

if [ $PYTHON_EXIT_CODE -ne 0 ]; then
    log "ERROR: Python script failed with exit code ${PYTHON_EXIT_CODE}"
    deactivate
    exit 1
fi

# Deactivate virtual environment
log "Deactivating virtual environment"
deactivate

log "SDR Workflow Runner completed successfully"
exit 0