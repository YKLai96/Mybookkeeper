import logging
from logging.handlers import RotatingFileHandler
import os

# Ensure the logs directory exists in the project root
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logger():
    # Create global Logger named JBoss_Finance
    logger = logging.getLogger("JBoss_Finance")
    
    # Set minimum log level (INFO and above will be recorded)
    logger.setLevel(logging.INFO)

    # 1. Console Handler (For real-time viewing in VSCode terminal)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 2. File Handler (Persistent storage, max 5MB, keep 3 backup files)
    log_file = os.path.join(LOG_DIR, "system.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 3. Standardize log format (Time - Level - Module - Message)
    formatter = logging.Formatter(
        fmt='%(asctime)s - [%(levelname)s] - %(module)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 4. Mount handlers (Prevent duplicate mounting)
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger

# Instantiate globally accessible logger
logger = setup_logger()