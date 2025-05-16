"""
Utility functions for structured logging.
"""
import logging
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s] %(message)s')
console_handler.setFormatter(console_formatter)
root_logger.addHandler(console_handler)

# File handler with rotation
file_handler = RotatingFileHandler(
    "logs/app.log", 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
root_logger.addHandler(file_handler)

# Create a separate logger for Firecrawl API
firecrawl_logger = logging.getLogger("firecrawl_api")
firecrawl_logger.setLevel(logging.INFO)

# File handler for Firecrawl API with rotation
firecrawl_file_handler = RotatingFileHandler(
    "logs/firecrawl_api.log", 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
firecrawl_file_handler.setLevel(logging.INFO)
firecrawl_file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
firecrawl_file_handler.setFormatter(firecrawl_file_formatter)
firecrawl_logger.addHandler(firecrawl_file_handler)

# Dictionary to store correlation IDs
correlation_ids = {}

def get_correlation_id(request_id: Optional[str] = None) -> str:
    """
    Get or create a correlation ID for the current request.
    
    Args:
        request_id (Optional[str]): Optional existing request ID
        
    Returns:
        str: Correlation ID
    """
    if request_id:
        correlation_ids[request_id] = request_id
        return request_id
    
    # Generate a new correlation ID
    new_id = str(uuid.uuid4())
    correlation_ids[new_id] = new_id
    return new_id

def clear_correlation_id(correlation_id: str) -> None:
    """
    Clear a correlation ID from the dictionary.
    
    Args:
        correlation_id (str): Correlation ID to clear
    """
    if correlation_id in correlation_ids:
        del correlation_ids[correlation_id]

def log_firecrawl_request(
    correlation_id: str,
    url: str,
    method: str,
    payload: Dict[str, Any],
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a Firecrawl API request.
    
    Args:
        correlation_id (str): Correlation ID
        url (str): Request URL
        method (str): HTTP method
        payload (Dict[str, Any]): Request payload
        additional_info (Optional[Dict[str, Any]]): Additional information to log
    """
    log_data = {
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "request",
        "url": url,
        "method": method,
        "payload_size": len(json.dumps(payload))
    }
    
    # Don't log the actual API key
    if "headers" in payload and "Authorization" in payload["headers"]:
        payload["headers"]["Authorization"] = "Bearer [REDACTED]"
    
    # Add additional info if provided
    if additional_info:
        log_data.update(additional_info)
    
    firecrawl_logger.info(json.dumps(log_data))

def log_firecrawl_response(
    correlation_id: str,
    url: str,
    status_code: int,
    response_time: float,
    response_size: int,
    cache_hit: bool = False,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a Firecrawl API response.
    
    Args:
        correlation_id (str): Correlation ID
        url (str): Request URL
        status_code (int): HTTP status code
        response_time (float): Response time in seconds
        response_size (int): Response size in bytes
        cache_hit (bool): Whether the response was from cache
        additional_info (Optional[Dict[str, Any]]): Additional information to log
    """
    log_data = {
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "response",
        "url": url,
        "status_code": status_code,
        "response_time_ms": round(response_time * 1000, 2),
        "response_size_bytes": response_size,
        "cache_hit": cache_hit
    }
    
    # Add additional info if provided
    if additional_info:
        log_data.update(additional_info)
    
    firecrawl_logger.info(json.dumps(log_data))

def log_firecrawl_error(
    correlation_id: str,
    url: str,
    error_type: str,
    error_message: str,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a Firecrawl API error.
    
    Args:
        correlation_id (str): Correlation ID
        url (str): Request URL
        error_type (str): Type of error
        error_message (str): Error message
        additional_info (Optional[Dict[str, Any]]): Additional information to log
    """
    log_data = {
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "error",
        "url": url,
        "error_type": error_type,
        "error_message": error_message
    }
    
    # Add additional info if provided
    if additional_info:
        log_data.update(additional_info)
    
    firecrawl_logger.error(json.dumps(log_data))
