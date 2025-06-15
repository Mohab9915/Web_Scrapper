"""
Utility functions for system resource checking.
"""
import os
import psutil
import platform
from typing import Dict, Any

def check_system_resources() -> Dict[str, Any]:
    """
    Check if the system has enough resources to run browser automation.
    
    Returns:
        Dict[str, Any]: Dictionary with system resource information and status
    """
    try:
        # Get system memory info
        memory = psutil.virtual_memory()
        available_memory_gb = round(memory.available / (1024 * 1024 * 1024), 2)
        
        # Get CPU load
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # Get disk space
        disk = psutil.disk_usage('/')
        free_disk_gb = round(disk.free / (1024 * 1024 * 1024), 2)
        
        # Check if we're running in a container with limited resources
        in_container = os.path.exists('/.dockerenv')
        
        # Determine if resources are sufficient
        has_sufficient_memory = available_memory_gb >= 1.0  # At least 1GB free
        has_sufficient_cpu = cpu_percent < 90             # CPU not completely overloaded
        has_sufficient_disk = free_disk_gb >= 1.0         # At least 1GB free disk
        
        return {
            "system": platform.system(),
            "release": platform.release(),
            "available_memory_gb": available_memory_gb,
            "cpu_percent": cpu_percent,
            "free_disk_gb": free_disk_gb,
            "in_container": in_container,
            "has_sufficient_resources": has_sufficient_memory and has_sufficient_cpu and has_sufficient_disk,
            "resource_issues": {
                "memory": not has_sufficient_memory,
                "cpu": not has_sufficient_cpu,
                "disk": not has_sufficient_disk
            }
        }
    except Exception as e:
        # If we can't check resources, assume they're sufficient but log the error
        # Consider logging this error using the application's logger
        return {
            "has_sufficient_resources": True,
            "error": str(e)
        }
