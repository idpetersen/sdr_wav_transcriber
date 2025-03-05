#!/usr/bin/env python3
import logging
from datetime import datetime
from pathlib import Path

class SDRWorkflowLogger:
    """
    Custom logging class to handle both file and console logging
    with different log levels and formatted output.
    """
    def __init__(self, log_dir, log_level=logging.INFO):
        """
        Initialize logger with file and console handlers.
        
        :param log_dir: Directory to store log files
        :param log_level: Logging level (default: INFO)
        """
        # Ensure log directory exists
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('SDRWorkflow')
        self.logger.setLevel(log_level)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create file handler
        log_file = self.log_dir / f"sdr_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # Set formatters
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """
        Return the configured logger.
        
        :return: Configured logging object
        """
        return self.logger