"""
Memory monitoring utilities for tracking memory usage and detecting leaks
"""

import gc
import psutil
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Memory monitoring utility for tracking memory usage and detecting leaks"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.baseline_memory = self.get_memory_usage()
        self.peak_memory = self.baseline_memory
        self.checkpoints = {}
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024
        except Exception as e:
            logger.warning(f"Could not get memory usage: {e}")
            return 0.0
    
    def log_memory_usage(self, stage: str, force_gc: bool = False) -> float:
        """Log current memory usage for a specific stage"""
        if force_gc:
            gc.collect()
        
        current_memory = self.get_memory_usage()
        self.peak_memory = max(self.peak_memory, current_memory)
        
        # Store checkpoint
        self.checkpoints[stage] = {
            'memory_mb': current_memory,
            'timestamp': datetime.now(timezone.utc),
            'peak_memory': self.peak_memory
        }
        
        logger.info(f"Memory usage at {stage}: {current_memory:.2f} MB (peak: {self.peak_memory:.2f} MB)")
        return current_memory
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        current_memory = self.get_memory_usage()
        
        return {
            'current_memory_mb': current_memory,
            'peak_memory_mb': self.peak_memory,
            'baseline_memory_mb': self.baseline_memory,
            'memory_increase_mb': current_memory - self.baseline_memory,
            'peak_increase_mb': self.peak_memory - self.baseline_memory,
            'checkpoints': self.checkpoints
        }
    
    def check_memory_leak(self, threshold_mb: float = 100.0) -> bool:
        """Check if memory usage has increased significantly (potential leak)"""
        current_memory = self.get_memory_usage()
        increase = current_memory - self.baseline_memory
        
        if increase > threshold_mb:
            logger.warning(f"Potential memory leak detected: {increase:.2f} MB increase from baseline")
            return True
        
        return False
    
    def force_cleanup(self) -> float:
        """Force garbage collection and return memory after cleanup"""
        logger.info("Forcing memory cleanup...")
        
        # Multiple garbage collection passes
        for i in range(3):
            collected = gc.collect()
            logger.info(f"GC pass {i+1}: collected {collected} objects")
        
        memory_after = self.get_memory_usage()
        logger.info(f"Memory after cleanup: {memory_after:.2f} MB")
        
        return memory_after
    
    def reset_baseline(self):
        """Reset baseline memory to current usage"""
        self.baseline_memory = self.get_memory_usage()
        self.peak_memory = self.baseline_memory
        logger.info(f"Reset memory baseline to: {self.baseline_memory:.2f} MB")

# Global memory monitor instance
memory_monitor = MemoryMonitor()

def log_memory_usage(stage: str, force_gc: bool = False) -> float:
    """Convenience function for logging memory usage"""
    return memory_monitor.log_memory_usage(stage, force_gc)

def get_memory_stats() -> Dict[str, Any]:
    """Convenience function for getting memory statistics"""
    return memory_monitor.get_memory_stats()

def check_memory_leak(threshold_mb: float = 100.0) -> bool:
    """Convenience function for checking memory leaks"""
    return memory_monitor.check_memory_leak(threshold_mb)

def force_cleanup() -> float:
    """Convenience function for forcing memory cleanup"""
    return memory_monitor.force_cleanup()
