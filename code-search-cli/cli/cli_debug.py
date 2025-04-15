"""
Debug utility to track execution flow in the CLI.
This will print directly to stdout for maximum visibility.
"""

import sys
import os
import time
import inspect
from datetime import datetime

# Set to True to enable debug logs
DEBUG_ENABLED = True

# Log levels
LEVELS = {
    "TRACE": 0,  # Most detailed
    "DEBUG": 1,  # Normal debugging
    "INFO": 2,   # Important information
    "WARN": 3,   # Warnings
    "ERROR": 4   # Errors
}

# Current log level - only logs at this level or higher will be shown
CURRENT_LEVEL = "TRACE"

def log(level, message, *args):
    """Log a message at the specified level."""
    if not DEBUG_ENABLED:
        return
        
    if LEVELS.get(level, 0) < LEVELS.get(CURRENT_LEVEL, 0):
        return
        
    # Format message with args
    if args:
        message = message.format(*args)
    
    # Get calling frame info
    caller = inspect.currentframe().f_back
    filename = os.path.basename(caller.f_code.co_filename)
    lineno = caller.f_lineno
    function = caller.f_code.co_name
    
    # Format timestamp
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # Print directly to stdout to bypass any formatting
    sys.stdout.write(f"[{timestamp}] {level:5} {filename}:{lineno} {function}() - {message}\n")
    sys.stdout.flush()

def trace(message, *args):
    """Log a trace message."""
    log("TRACE", message, *args)
    
def debug(message, *args):
    """Log a debug message."""
    log("DEBUG", message, *args)
    
def info(message, *args):
    """Log an info message."""
    log("INFO", message, *args)
    
def warn(message, *args):
    """Log a warning message."""
    log("WARN", message, *args)
    
def error(message, *args):
    """Log an error message."""
    log("ERROR", message, *args)

def set_level(level):
    """Set the current log level."""
    global CURRENT_LEVEL
    if level in LEVELS:
        CURRENT_LEVEL = level
        info("Log level set to {}", level)
    else:
        warn("Invalid log level: {}", level)
        
def enable():
    """Enable debug logging."""
    global DEBUG_ENABLED
    DEBUG_ENABLED = True
    info("Debug logging enabled")
    
def disable():
    """Disable debug logging."""
    global DEBUG_ENABLED
    DEBUG_ENABLED = False