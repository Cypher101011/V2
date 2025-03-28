"""
Resource management for EPUB2TTS
"""

import os
import sys
import time
import logging
import tempfile
import threading
import multiprocessing
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not installed. Resource monitoring will be limited.")

# Resource limits
DEFAULT_MEMORY_LIMIT_MB = 1024  # 1 GB
DEFAULT_DISK_LIMIT_GB = 5  # 5 GB
DEFAULT_CPU_LIMIT_PERCENT = 80  # 80% CPU usage


class ResourceMonitor:
    """Monitor system resources"""
    
    def __init__(self, memory_limit_mb=DEFAULT_MEMORY_LIMIT_MB, 
                 disk_limit_gb=DEFAULT_DISK_LIMIT_GB,
                 cpu_limit_percent=DEFAULT_CPU_LIMIT_PERCENT):
        """
        Initialize resource monitor
        
        Args:
            memory_limit_mb (int): Memory limit in MB
            disk_limit_gb (int): Disk limit in GB
            cpu_limit_percent (int): CPU limit in percent
        """
        self.memory_limit_mb = memory_limit_mb
        self.disk_limit_gb = disk_limit_gb
        self.cpu_limit_percent = cpu_limit_percent
        
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks = []
        
        # Resource usage history
        self.memory_history = []
        self.disk_history = []
        self.cpu_history = []
        
        # Check if psutil is available
        self.psutil_available = PSUTIL_AVAILABLE
    
    def start_monitoring(self, interval=1.0):
        """
        Start monitoring resources
        
        Args:
            interval (float): Monitoring interval in seconds
        """
        if not self.psutil_available:
            logger.warning("psutil not installed. Resource monitoring not available.")
            return False
        
        if self.monitoring:
            logger.warning("Resource monitoring already started")
            return False
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Resource monitoring started")
        return True
    
    def stop_monitoring(self):
        """Stop monitoring resources"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None
        
        logger.info("Resource monitoring stopped")
    
    def _monitor_resources(self, interval):
        """
        Monitor resources
        
        Args:
            interval (float): Monitoring interval in seconds
        """
        while self.monitoring:
            try:
                # Get memory usage
                memory = psutil.virtual_memory()
                memory_used_mb = (memory.total - memory.available) / (1024 * 1024)
                memory_percent = memory.percent
                
                # Get disk usage
                disk = psutil.disk_usage('/')
                disk_used_gb = (disk.total - disk.free) / (1024 * 1024 * 1024)
                disk_percent = disk.percent
                
                # Get CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Add to history (keep last 60 samples)
                self.memory_history.append(memory_used_mb)
                self.disk_history.append(disk_used_gb)
                self.cpu_history.append(cpu_percent)
                
                if len(self.memory_history) > 60:
                    self.memory_history.pop(0)
                if len(self.disk_history) > 60:
                    self.disk_history.pop(0)
                if len(self.cpu_history) > 60:
                    self.cpu_history.pop(0)
                
                # Check if resources are exceeded
                memory_exceeded = memory_used_mb > self.memory_limit_mb
                disk_exceeded = disk_used_gb > self.disk_limit_gb
                cpu_exceeded = cpu_percent > self.cpu_limit_percent
                
                if memory_exceeded or disk_exceeded or cpu_exceeded:
                    # Call callbacks
                    for callback in self.callbacks:
                        try:
                            callback(memory_used_mb, disk_used_gb, cpu_percent)
                        except Exception as e:
                            logger.error(f"Error in resource monitor callback: {str(e)}")
                
                # Sleep for interval
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"Error monitoring resources: {str(e)}")
                time.sleep(interval)
    
    def add_callback(self, callback):
        """
        Add callback for resource limit exceeded
        
        Args:
            callback: Callback function(memory_used_mb, disk_used_gb, cpu_percent)
        """
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """
        Remove callback
        
        Args:
            callback: Callback function to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_resource_usage(self):
        """
        Get current resource usage
        
        Returns:
            dict: Resource usage
        """
        if not self.psutil_available:
            return {
                'memory_used_mb': 0,
                'memory_percent': 0,
                'disk_used_gb': 0,
                'disk_percent': 0,
                'cpu_percent': 0,
                'available': False
            }
        
        try:
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_used_mb = (memory.total - memory.available) / (1024 * 1024)
            memory_percent = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_used_gb = (disk.total - disk.free) / (1024 * 1024 * 1024)
            disk_percent = disk.percent
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            return {
                'memory_used_mb': memory_used_mb,
                'memory_percent': memory_percent,
                'disk_used_gb': disk_used_gb,
                'disk_percent': disk_percent,
                'cpu_percent': cpu_percent,
                'available': True
            }
        
        except Exception as e:
            logger.error(f"Error getting resource usage: {str(e)}")
            return {
                'memory_used_mb': 0,
                'memory_percent': 0,
                'disk_used_gb': 0,
                'disk_percent': 0,
                'cpu_percent': 0,
                'available': False,
                'error': str(e)
            }
    
    def get_resource_history(self):
        """
        Get resource usage history
        
        Returns:
            dict: Resource history
        """
        return {
            'memory_history': self.memory_history.copy(),
            'disk_history': self.disk_history.copy(),
            'cpu_history': self.cpu_history.copy()
        }


class TempFileManager:
    """Manage temporary files"""
    
    def __init__(self, base_dir=None, prefix="epub2tts_"):
        """
        Initialize temp file manager
        
        Args:
            base_dir (str, optional): Base directory for temp files
            prefix (str): Prefix for temp files
        """
        self.base_dir = base_dir
        self.prefix = prefix
        self.temp_dirs = []
        self.temp_files = []
    
    def create_temp_dir(self):
        """
        Create temporary directory
        
        Returns:
            str: Path to temporary directory
        """
        temp_dir = tempfile.mkdtemp(prefix=self.prefix, dir=self.base_dir)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_file(self, suffix=None):
        """
        Create temporary file
        
        Args:
            suffix (str, optional): File suffix
            
        Returns:
            str: Path to temporary file
        """
        temp_file = tempfile.NamedTemporaryFile(
            prefix=self.prefix, 
            suffix=suffix,
            dir=self.base_dir,
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()
        
        self.temp_files.append(temp_path)
        return temp_path
    
    def cleanup(self, remove_dirs=True, remove_files=True):
        """
        Clean up temporary files and directories
        
        Args:
            remove_dirs (bool): Whether to remove directories
            remove_files (bool): Whether to remove files
        """
        # Remove temp files
        if remove_files:
            for file_path in self.temp_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp file {file_path}: {str(e)}")
            
            self.temp_files = []
        
        # Remove temp directories
        if remove_dirs:
            for dir_path in self.temp_dirs:
                try:
                    if os.path.exists(dir_path):
                        # Remove all files in directory
                        for file in os.listdir(dir_path):
                            file_path = os.path.join(dir_path, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                        
                        # Remove directory
                        os.rmdir(dir_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp directory {dir_path}: {str(e)}")
            
            self.temp_dirs = []
    
    def __del__(self):
        """Clean up on deletion"""
        self.cleanup()


class ProcessManager:
    """Manage processes"""
    
    def __init__(self, max_processes=None):
        """
        Initialize process manager
        
        Args:
            max_processes (int, optional): Maximum number of processes
        """
        if max_processes is None:
            # Use number of CPU cores
            max_processes = multiprocessing.cpu_count()
        
        self.max_processes = max_processes
        self.processes = []
    
    def start_process(self, target, args=(), kwargs=None):
        """
        Start process
        
        Args:
            target: Target function
            args: Arguments
            kwargs: Keyword arguments
            
        Returns:
            multiprocessing.Process: Process object
        """
        if kwargs is None:
            kwargs = {}
        
        # Wait if max processes reached
        while len(self.processes) >= self.max_processes:
            # Remove finished processes
            self.processes = [p for p in self.processes if p.is_alive()]
            
            if len(self.processes) >= self.max_processes:
                time.sleep(0.1)
        
        # Start process
        process = multiprocessing.Process(target=target, args=args, kwargs=kwargs)
        process.daemon = True
        process.start()
        
        self.processes.append(process)
        return process
    
    def wait_for_all(self, timeout=None):
        """
        Wait for all processes to finish
        
        Args:
            timeout (float, optional): Timeout in seconds
            
        Returns:
            bool: True if all processes finished, False if timeout
        """
        start_time = time.time()
        
        while self.processes:
            # Remove finished processes
            self.processes = [p for p in self.processes if p.is_alive()]
            
            if not self.processes:
                return True
            
            # Check timeout
            if timeout is not None and time.time() - start_time > timeout:
                return False
            
            time.sleep(0.1)
        
        return True
    
    def terminate_all(self):
        """Terminate all processes"""
        for process in self.processes:
            if process.is_alive():
                process.terminate()
        
        # Wait for processes to terminate
        for process in self.processes:
            process.join(timeout=1.0)
        
        self.processes = []


# Global instances
resource_monitor = ResourceMonitor()
temp_file_manager = TempFileManager()
process_manager = ProcessManager()

