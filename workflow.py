#!/usr/bin/env python3
import os
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path

import paramiko
import whisper

from logger import SDRWorkflowLogger
from claude_handler import ClaudeHandler

class SDRTranscriptionWorkflow:
    def __init__(self, config, cleanup=False, log_level=logging.INFO):
        """
        Initialize the SDR transcription workflow with configuration.
        
        :param config: Dictionary containing configuration parameters
        :param cleanup: Boolean to determine if remote recordings dir should be cleaned
        :param log_level: Logging level (default: INFO)
        """
        # Setup logging
        logger_manager = SDRWorkflowLogger(
            log_dir=config.get('log_dir', os.path.expanduser('~/sdr_workflow/logs')),
            log_level=log_level
        )
        self.logger = logger_manager.get_logger()
        
        self.config = config
        self.cleanup = cleanup
        self.ssh_client = None
        self.sftp_client = None
        
        # Log initialization
        self.logger.info("Initializing SDR Transcription Workflow")
        self.logger.debug(f"Configuration: {config}")
        self.logger.debug(f"Cleanup mode: {cleanup}")
        
        # Setup local paths
        self.base_dir = Path(config.get('base_dir', os.path.expanduser('~/sdr_workflow')))
        self.recordings_dir = self.base_dir / 'recordings'
        self.transcripts_dir = self.base_dir / 'transcripts'
        self.summaries_dir = self.base_dir / 'daily_summaries'
        
        # Create necessary directories with logging
        for dir_path in [self.recordings_dir, self.transcripts_dir, self.summaries_dir]:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created directory: {dir_path}")
            except Exception as e:
                self.logger.error(f"Failed to create directory {dir_path}: {e}")
                raise
        
        # Validate SSH key
        key_path = Path(config['key_path'])
        if not key_path.exists():
            self.logger.critical(f"SSH key not found at {key_path}")
            raise FileNotFoundError(f"SSH key not found at {key_path}")
        
        # Setup Whisper model with error handling
        try:
            whisper_model = config.get('whisper_model', 'medium.en')
            self.logger.info(f"Loading Whisper model: {whisper_model}")
            self.whisper_model = whisper.load_model(whisper_model)
        except Exception as e:
            self.logger.critical(f"Failed to load Whisper model: {e}")
            raise
        
        # Initialize Claude handler
        self.claude_handler = ClaudeHandler(
            logger=self.logger,
            base_dir=self.base_dir,
            api_key=config.get('claude_api_key', ''),
            model=config.get('claude_model', 'claude-3-7-sonnet-20250219'),
            max_tokens=config.get('max_tokens', 300),
            temperature=config.get('temperature', 0.7)
        )

    def connect_to_remote(self):
        """
        Establish SSH and SFTP connections to the remote host.
        """
        try:
            # Create SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Load SSH key
            key_path = self.config['key_path']
            private_key = paramiko.RSAKey.from_private_key_file(key_path)
            
            # Connect to host
            self.ssh_client.connect(
                hostname=self.config['host'],
                username=self.config['username'],
                pkey=private_key
            )
            
            # Create SFTP client
            self.sftp_client = self.ssh_client.open_sftp()
            
            self.logger.info(f"Connected to {self.config['host']} successfully")
        
        except Exception as e:
            self.logger.error(f"SSH connection error: {e}")
            self.logger.debug(traceback.format_exc())
            raise

    def download_latest_wav(self):
        """
        Download the latest WAV file from the remote host.
        
        :return: Path to the downloaded WAV file or None
        """
        try:
            # Change to remote recordings directory
            self.sftp_client.chdir(self.config['remote_dir'])
            
            # Get list of WAV files sorted by modification time
            wav_files = [f for f in self.sftp_client.listdir() if f.endswith('.wav')]
            
            if not wav_files:
                self.logger.warning("No WAV files found in remote directory")
                return None
            
            # Get the latest WAV file
            latest_wav = max(wav_files, key=lambda f: 
                self.sftp_client.stat(f).st_mtime
            )
            
            # Local path for download
            local_path = self.recordings_dir / latest_wav
            
            # Download file
            self.sftp_client.get(latest_wav, str(local_path))
            
            self.logger.info(f"Downloaded WAV file: {local_path}")
            return local_path
        
        except Exception as e:
            self.logger.error(f"WAV download error: {e}")
            self.logger.debug(traceback.format_exc())
            return None

    def archive_remote_recordings(self):
        """
        Move remote recordings to archive directory after download.
        """
        if not self.cleanup:
            return
        try:
            remote_dir = self.config['remote_dir']
            archive_dir = os.path.join(os.path.dirname(remote_dir.rstrip('/')), 'archive')
            
            # Check if archive directory exists, create if not
            try:
                self.sftp_client.stat(archive_dir)
            except FileNotFoundError:
                self.sftp_client.mkdir(archive_dir)
                self.logger.info(f"Created archive directory: {archive_dir}")
            
            # Change to remote recordings directory
            self.sftp_client.chdir(remote_dir)
            
            # Move WAV files to archive
            wav_files = [f for f in self.sftp_client.listdir() if f.endswith('.wav')]
            for wav_file in wav_files:
                self.sftp_client.rename(
                    os.path.join(remote_dir, wav_file),
                    os.path.join(archive_dir, wav_file)
                )
            
            self.logger.info(f"Archived {len(wav_files)} WAV files to {archive_dir}")
        except Exception as e:
            self.logger.error(f"Error archiving remote recordings: {e}")
            self.logger.debug(traceback.format_exc())

    def transcribe_wav(self, wav_path):
        """
        Transcribe WAV file using Whisper with timestamped output.
        
        :param wav_path: Path to WAV file
        :return: Transcribed text or None
        """
        try:
            # Transcribe audio with segments
            self.logger.info(f"Starting transcription on file {wav_path}")
            result = self.whisper_model.transcribe(str(wav_path), language='en', verbose=False)
            
            # Format transcript with timestamps
            formatted_transcript = ""
            for segment in result['segments']:
                start_time = segment['start']
                end_time = segment['end']
                text = segment['text'].strip()
                
                # Format timestamp as [MM:SS.mmm --> MM:SS.mmm]
                start_formatted = f"{int(start_time//60):02d}:{start_time%60:06.3f}"
                end_formatted = f"{int(end_time//60):02d}:{end_time%60:06.3f}"
                
                # Add formatted line
                formatted_transcript += f"[{start_formatted} --> {end_formatted}]  {text}\n"
            
            # Save raw JSON result for analysis if needed
            json_path = self.transcripts_dir / f"{wav_path.stem}_transcript.json"
            with open(json_path, 'w') as f:
                json.dump(result, f, indent=4)
            
            # Save formatted transcript
            transcript_path = self.transcripts_dir / f"{wav_path.stem}_transcript.txt"
            with open(transcript_path, 'w') as f:
                f.write(formatted_transcript)
            
            self.logger.info(f"Transcription complete. Saved to {transcript_path}")
            return formatted_transcript
        
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            self.logger.debug(traceback.format_exc())
            return None

    def generate_summary(self, transcript):
        """
        Generate summary using Claude handler.
        
        :param transcript: Text to summarize
        :return: Generated summary or None
        """
        return self.claude_handler.generate_summary(transcript)

    def save_summary(self, summary):
        """
        Save daily summary to file.
        
        :param summary: Summary text
        """
        try:
            # Generate filename with current date
            summary_filename = f"summary_{datetime.now().strftime('%Y%m%d')}.md"
            summary_path = self.summaries_dir / summary_filename
            
            # Write summary
            with open(summary_path, 'w') as f:
                f.write(summary)
            
            self.logger.info(f"Summary saved to {summary_path}")
        
        except Exception as e:
            self.logger.error(f"Error saving summary: {e}")
            self.logger.debug(traceback.format_exc())

    def run_workflow(self):
        """
        Execute the complete SDR transcription workflow with comprehensive error handling.
        """
        try:
            self.logger.info("Starting SDR Transcription Workflow")
            
            # Connect to remote host
            self.connect_to_remote()
            
            # Download latest WAV
            wav_path = self.download_latest_wav()
            if not wav_path:
                self.logger.warning("No WAV file downloaded. Exiting workflow.")
                return
            
            # Optionally clear remote recordings
            self.clear_remote_recordings()
            
            # Transcribe WAV
            transcript = self.transcribe_wav(wav_path)
            if not transcript:
                self.logger.warning("Transcription failed. Exiting workflow.")
                return
            
            # Generate summary using Claude API
            summary = self.generate_summary(transcript)
            if summary:
                # Save summary
                self.save_summary(summary)
            else:
                self.logger.warning("Summary generation failed.")
        
        except Exception as e:
            self.logger.critical(f"Workflow error: {e}")
            self.logger.debug(traceback.format_exc())
        
        finally:
            # Always attempt to close connections
            try:
                if self.sftp_client:
                    self.sftp_client.close()
                if self.ssh_client:
                    self.ssh_client.close()
                self.logger.info("SSH connections closed")
            except Exception as close_error:
                self.logger.error(f"Error closing SSH connections: {close_error}")