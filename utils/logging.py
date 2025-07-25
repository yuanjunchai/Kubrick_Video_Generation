import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(log_file: Optional[str] = None, 
                 verbose: bool = False,
                 log_dir: str = "./logs") -> logging.Logger:
    """Setup logging configuration
    
    Args:
        log_file: Optional log file path
        verbose: Enable verbose (DEBUG) logging
        log_dir: Directory for log files
    
    Returns:
        Configured logger
    """
    
    # Create log directory if needed
    if log_file or log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        if not log_file:
            # Generate log filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_path / f"kubrick_{timestamp}.log"
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Console formatter with colors
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(name_colored)s - %(levelname_colored)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if log file specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Log startup information
    logger.info("="*60)
    logger.info("Kubrick Video Generation System")
    logger.info("="*60)
    if log_file:
        logger.info(f"Logging to: {log_file}")
    
    return logger


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    
    RESET = '\033[0m'
    
    def format(self, record):
        # Add colored level name
        levelname_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname_colored = f"{levelname_color}{record.levelname}{self.RESET}"
        
        # Add colored logger name (abbreviated)
        name_parts = record.name.split('.')
        if len(name_parts) > 1:
            # Abbreviate module names
            abbreviated = '.'.join(p[0] for p in name_parts[:-1]) + '.' + name_parts[-1]
        else:
            abbreviated = record.name
        
        record.name_colored = f"\033[34m{abbreviated}\033[0m"  # Blue
        
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)