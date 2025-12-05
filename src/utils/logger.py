"""
Logging utilities for the crawler
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str = "nextjs_crawler",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Setup a logger with file and console handlers

    Args:
        name: Logger name
        level: Logging level
        log_file: Path to log file (optional)
        console: Whether to log to console

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_default_log_file() -> str:
    """Get default log file path with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    return str(log_dir / f'crawler_{timestamp}.log')


class ProgressLogger:
    """Logger for tracking crawler progress"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.stats = {
            'total_processed': 0,
            'nextjs_found': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    def log_processed(self, url: str, is_nextjs: bool = False):
        """Log a processed URL"""
        self.stats['total_processed'] += 1
        if is_nextjs:
            self.stats['nextjs_found'] += 1

    def log_error(self, url: str, error: Exception):
        """Log an error"""
        self.stats['errors'] += 1
        self.logger.error(f"Error processing {url}: {error}")

    def log_stats(self):
        """Log current statistics"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        rate = self.stats['total_processed'] / elapsed if elapsed > 0 else 0

        self.logger.info(
            f"Stats - Processed: {self.stats['total_processed']}, "
            f"Next.js found: {self.stats['nextjs_found']}, "
            f"Errors: {self.stats['errors']}, "
            f"Rate: {rate:.2f} URLs/sec"
        )

    def get_stats(self) -> dict:
        """Get current statistics"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        return {
            **self.stats,
            'elapsed_seconds': elapsed,
            'rate_per_second': self.stats['total_processed'] / elapsed if elapsed > 0 else 0
        }
