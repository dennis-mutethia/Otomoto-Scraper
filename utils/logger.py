from __future__ import annotations

import logging
import os

file_logger = logging.getLogger('file_logger')
file_logger.setLevel(logging.INFO)

console_logger = logging.getLogger('console_logger')
console_logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - [%(name)s] - [%(levelname)s] - %(message)s')
console_handler.setFormatter(formatter)
console_logger.addHandler(console_handler)

try:
    os.makedirs('output/logs', exist_ok=True)
    file_handler = logging.FileHandler('output/logs/app.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_logger.addHandler(file_handler)
    console_logger.info("File logging setup successful.")
except Exception as e:
    console_logger.warning(f"Failed to set up file logging: {e}")
    # file_logger will continue without file handler