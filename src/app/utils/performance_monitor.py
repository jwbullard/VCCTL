#!/usr/bin/env python3
"""
Performance Monitoring Utilities for VCCTL

Provides performance profiling, memory leak detection, and optimization
tools for the VCCTL application.
"""

import logging
import time
import threading
import gc
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import functools


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    timestamp: float
    metric_name: str
    value: Union[float, int]
    unit: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FunctionProfile:
    """Performance profile for a function."""
    function_name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_called: Optional[float] = None
    
    def add_call(self, duration: float) -> None:
        """Add a function call timing."""
        self.call_count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.call_count
        self.last_called = time.time()


@dataclass
class MemorySnapshot:
    """Memory usage snapshot."""
    timestamp: float
    rss_memory: float  # Resident set size in MB
    vms_memory: float  # Virtual memory size in MB
    memory_percent: float
    available_memory: float
    gc_counts: Dict[int, int]  # Garbage collection counts by generation
    object_counts: Dict[str, int] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Performance monitoring and profiling system for VCCTL.
    
    Features:
    - Function call profiling
    - Memory usage tracking
    - Memory leak detection
    - Performance metrics collection
    - Automated optimization suggestions
    """
    
    def __init__(self, enabled: bool = True):
        """Initialize performance monitor."""
        self.logger = logging.getLogger('VCCTL.PerformanceMonitor')
        self.enabled = enabled
        
        if not self.enabled:
            return
        
        # Metrics storage
        self.metrics: List[PerformanceMetric] = []
        self.function_profiles: Dict[str, FunctionProfile] = {}
        self.memory_snapshots: deque = deque(maxlen=1000)  # Keep last 1000 snapshots
        
        # Monitoring configuration
        self.max_metrics = 10000
        self.snapshot_interval = 30.0  # seconds
        self.profile_threshold = 0.001  # Only profile functions taking >1ms
        
        # Performance thresholds
        self.thresholds = {
            'function_call_time': 1.0,  # seconds
            'memory_growth_rate': 50.0,  # MB per minute
            'memory_usage_percent': 80.0,  # percentage
            'gc_frequency': 100  # collections per minute
        }
        
        # Monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        # Performance alerts
        self.alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # Try to import psutil for system metrics
        self.psutil_available = False
        try:
            import psutil
            self.psutil = psutil
            self.psutil_available = True
        except ImportError:
            self.logger.warning("psutil not available - system metrics will be limited")
        
        self.logger.info("Performance monitor initialized")
    
    def start_monitoring(self) -> None:
        """Start background monitoring."""
        if not self.enabled or self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=2.0)
            self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Take memory snapshot
                self._take_memory_snapshot()
                
                # Check for performance issues
                self._check_performance_alerts()
                
                # Clean up old metrics
                self._cleanup_old_metrics()
                
                # Sleep until next iteration
                time.sleep(self.snapshot_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)  # Longer pause on error
    
    def add_metric(self, name: str, value: Union[float, int], unit: str = "", 
                  context: Optional[Dict[str, Any]] = None) -> None:
        """Add a performance metric."""
        if not self.enabled:
            return
        
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_name=name,
            value=value,
            unit=unit,
            context=context or {}
        )
        
        self.metrics.append(metric)
        
        # Clean up if too many metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics//2:]
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile function performance."""
        if not self.enabled:
            return func
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                
                # Only profile if duration exceeds threshold
                if duration >= self.profile_threshold:
                    function_name = f"{func.__module__}.{func.__name__}"
                    
                    if function_name not in self.function_profiles:
                        self.function_profiles[function_name] = FunctionProfile(function_name)
                    
                    self.function_profiles[function_name].add_call(duration)
                    
                    # Add as metric
                    self.add_metric(
                        f"function_call_time.{func.__name__}",
                        duration * 1000,  # Convert to milliseconds
                        "ms",
                        {"module": func.__module__, "args_count": len(args)}
                    )
        
        return wrapper
    
    def measure_time(self, name: str) -> 'TimeContextManager':
        """Context manager for measuring execution time."""
        return TimeContextManager(self, name)
    
    def _take_memory_snapshot(self) -> None:
        """Take a memory usage snapshot."""
        try:
            timestamp = time.time()
            
            if self.psutil_available:
                import os
                process = self.psutil.Process(os.getpid())
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                
                # Get system memory info
                system_memory = self.psutil.virtual_memory()
                
                rss_mb = memory_info.rss / 1024 / 1024
                vms_mb = memory_info.vms / 1024 / 1024
                available_mb = system_memory.available / 1024 / 1024
            else:
                # Fallback to basic metrics
                rss_mb = 0.0
                vms_mb = 0.0
                memory_percent = 0.0
                available_mb = 0.0
            
            # Get garbage collection stats
            gc_counts = {}
            try:
                for i in range(3):  # Python has 3 GC generations
                    gc_counts[i] = gc.get_count()[i]
            except:
                gc_counts = {0: 0, 1: 0, 2: 0}
            
            # Get object counts (sampling)
            object_counts = {}
            try:
                import sys
                all_objects = gc.get_objects()
                type_counts = defaultdict(int)
                
                # Sample every 100th object to avoid performance impact
                for i, obj in enumerate(all_objects):
                    if i % 100 == 0:
                        type_name = type(obj).__name__
                        type_counts[type_name] += 100  # Scale back up
                
                # Keep only top 10 types
                top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                object_counts = dict(top_types)
                
            except Exception as e:
                self.logger.debug(f"Failed to get object counts: {e}")
            
            snapshot = MemorySnapshot(
                timestamp=timestamp,
                rss_memory=rss_mb,
                vms_memory=vms_mb,
                memory_percent=memory_percent,
                available_memory=available_mb,
                gc_counts=gc_counts,
                object_counts=object_counts
            )
            
            self.memory_snapshots.append(snapshot)
            
            # Add metrics
            self.add_metric("memory.rss", rss_mb, "MB")
            self.add_metric("memory.vms", vms_mb, "MB")
            self.add_metric("memory.percent", memory_percent, "%")
            self.add_metric("memory.available", available_mb, "MB")
            
        except Exception as e:
            self.logger.error(f"Failed to take memory snapshot: {e}")
    
    def _check_performance_alerts(self) -> None:
        """Check for performance issues and trigger alerts."""
        try:
            current_time = time.time()
            
            # Check function call times
            for profile in self.function_profiles.values():
                if (profile.last_called and 
                    current_time - profile.last_called < 60 and  # Called in last minute
                    profile.avg_time > self.thresholds['function_call_time']):
                    
                    self._trigger_alert(
                        "slow_function",
                        {
                            "function": profile.function_name,
                            "avg_time": profile.avg_time,
                            "call_count": profile.call_count
                        }
                    )
            
            # Check memory growth
            if len(self.memory_snapshots) >= 2:
                recent_snapshots = list(self.memory_snapshots)[-10:]  # Last 10 snapshots
                if len(recent_snapshots) >= 2:
                    time_diff = recent_snapshots[-1].timestamp - recent_snapshots[0].timestamp
                    memory_diff = recent_snapshots[-1].rss_memory - recent_snapshots[0].rss_memory
                    
                    if time_diff > 0:
                        growth_rate = (memory_diff / time_diff) * 60  # MB per minute
                        
                        if growth_rate > self.thresholds['memory_growth_rate']:
                            self._trigger_alert(
                                "memory_growth",
                                {
                                    "growth_rate_mb_per_min": growth_rate,
                                    "current_memory_mb": recent_snapshots[-1].rss_memory
                                }
                            )
            
            # Check memory usage percentage
            if self.memory_snapshots:
                latest = self.memory_snapshots[-1]
                if latest.memory_percent > self.thresholds['memory_usage_percent']:
                    self._trigger_alert(
                        "high_memory_usage",
                        {
                            "memory_percent": latest.memory_percent,
                            "rss_memory_mb": latest.rss_memory
                        }
                    )
            
        except Exception as e:
            self.logger.error(f"Error checking performance alerts: {e}")
    
    def _trigger_alert(self, alert_type: str, details: Dict[str, Any]) -> None:
        """Trigger a performance alert."""
        self.logger.warning(f"Performance alert: {alert_type} - {details}")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, details)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")
    
    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics to prevent memory bloat."""
        if len(self.metrics) > self.max_metrics:
            # Keep the most recent half
            self.metrics = self.metrics[-self.max_metrics//2:]
        
        # Clean up function profiles that haven't been called recently
        cutoff_time = time.time() - 3600  # 1 hour
        profiles_to_remove = []
        
        for name, profile in self.function_profiles.items():
            if profile.last_called and profile.last_called < cutoff_time:
                profiles_to_remove.append(name)
        
        for name in profiles_to_remove:
            del self.function_profiles[name]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        current_time = time.time()
        
        # Function performance summary
        function_summary = {}
        for name, profile in self.function_profiles.items():
            function_summary[name] = {
                "call_count": profile.call_count,
                "total_time_ms": profile.total_time * 1000,
                "avg_time_ms": profile.avg_time * 1000,
                "min_time_ms": profile.min_time * 1000 if profile.min_time != float('inf') else 0,
                "max_time_ms": profile.max_time * 1000,
                "last_called": profile.last_called
            }
        
        # Memory summary
        memory_summary = {}
        if self.memory_snapshots:
            latest = self.memory_snapshots[-1]
            memory_summary = {
                "current_rss_mb": latest.rss_memory,
                "current_vms_mb": latest.vms_memory,
                "memory_percent": latest.memory_percent,
                "available_mb": latest.available_memory,
                "gc_counts": latest.gc_counts,
                "top_object_types": latest.object_counts
            }
            
            # Calculate memory growth if we have enough data
            if len(self.memory_snapshots) >= 10:
                older = self.memory_snapshots[-10]
                time_diff = latest.timestamp - older.timestamp
                memory_diff = latest.rss_memory - older.rss_memory
                
                if time_diff > 0:
                    memory_summary["growth_rate_mb_per_min"] = (memory_diff / time_diff) * 60
        
        # Metrics summary
        metrics_summary = {
            "total_metrics": len(self.metrics),
            "monitoring_duration_hours": (current_time - self.memory_snapshots[0].timestamp) / 3600 if self.memory_snapshots else 0
        }
        
        return {
            "timestamp": current_time,
            "functions": function_summary,
            "memory": memory_summary,
            "metrics": metrics_summary
        }
    
    def get_slowest_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the slowest functions by average time."""
        sorted_profiles = sorted(
            self.function_profiles.values(),
            key=lambda p: p.avg_time,
            reverse=True
        )
        
        return [
            {
                "name": profile.function_name,
                "avg_time_ms": profile.avg_time * 1000,
                "call_count": profile.call_count,
                "total_time_ms": profile.total_time * 1000
            }
            for profile in sorted_profiles[:limit]
        ]
    
    def get_memory_trend(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get memory usage trend for the specified hours."""
        cutoff_time = time.time() - (hours * 3600)
        
        trend_data = []
        for snapshot in self.memory_snapshots:
            if snapshot.timestamp >= cutoff_time:
                trend_data.append({
                    "timestamp": snapshot.timestamp,
                    "rss_mb": snapshot.rss_memory,
                    "vms_mb": snapshot.vms_memory,
                    "percent": snapshot.memory_percent
                })
        
        return trend_data
    
    def detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks."""
        leaks = []
        
        if len(self.memory_snapshots) < 10:
            return leaks
        
        # Check for consistent memory growth
        recent_snapshots = list(self.memory_snapshots)[-20:]  # Last 20 snapshots
        
        if len(recent_snapshots) >= 10:
            # Calculate trend
            memory_values = [s.rss_memory for s in recent_snapshots]
            time_values = [s.timestamp for s in recent_snapshots]
            
            # Simple linear regression
            n = len(memory_values)
            sum_xy = sum(t * m for t, m in zip(time_values, memory_values))
            sum_x = sum(time_values)
            sum_y = sum(memory_values)
            sum_x2 = sum(t * t for t in time_values)
            
            if n * sum_x2 - sum_x * sum_x != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                
                # Convert slope to MB per hour
                slope_mb_per_hour = slope * 3600
                
                if slope_mb_per_hour > 10:  # Growing by more than 10MB per hour
                    leaks.append({
                        "type": "memory_growth",
                        "growth_rate_mb_per_hour": slope_mb_per_hour,
                        "current_memory_mb": memory_values[-1],
                        "trend_duration_minutes": (time_values[-1] - time_values[0]) / 60
                    })
        
        # Check for object count growth
        if len(self.memory_snapshots) >= 5:
            recent = list(self.memory_snapshots)[-5:]
            
            # Look for objects that are consistently growing
            object_types = set()
            for snapshot in recent:
                object_types.update(snapshot.object_counts.keys())
            
            for obj_type in object_types:
                counts = []
                for snapshot in recent:
                    if obj_type in snapshot.object_counts:
                        counts.append(snapshot.object_counts[obj_type])
                
                if len(counts) >= 3 and all(counts[i] <= counts[i+1] for i in range(len(counts)-1)):
                    # Consistently growing
                    growth = counts[-1] - counts[0]
                    if growth > 1000:  # More than 1000 objects
                        leaks.append({
                            "type": "object_leak",
                            "object_type": obj_type,
                            "growth_count": growth,
                            "current_count": counts[-1]
                        })
        
        return leaks
    
    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add callback for performance alerts."""
        self.alert_callbacks.append(callback)
    
    def export_performance_data(self, output_file: Path) -> None:
        """Export all performance data to file."""
        try:
            data = {
                "export_timestamp": time.time(),
                "summary": self.get_performance_summary(),
                "slowest_functions": self.get_slowest_functions(20),
                "memory_trend": self.get_memory_trend(2),  # Last 2 hours
                "memory_leaks": self.detect_memory_leaks(),
                "raw_metrics": [
                    {
                        "timestamp": m.timestamp,
                        "name": m.metric_name,
                        "value": m.value,
                        "unit": m.unit,
                        "context": m.context
                    }
                    for m in self.metrics[-1000:]  # Last 1000 metrics
                ]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Performance data exported to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export performance data: {e}")


class TimeContextManager:
    """Context manager for measuring execution time."""
    
    def __init__(self, monitor: PerformanceMonitor, name: str):
        self.monitor = monitor
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitor.add_metric(
                f"timing.{self.name}",
                duration * 1000,  # Convert to milliseconds
                "ms"
            )


# Global performance monitor instance
_global_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor(enabled: bool = True) -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _global_performance_monitor
    
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor(enabled)
    
    return _global_performance_monitor


def profile_function(func: Callable) -> Callable:
    """Convenience decorator for function profiling."""
    return get_performance_monitor().profile_function(func)


def measure_time(name: str) -> TimeContextManager:
    """Convenience function for time measurement."""
    return get_performance_monitor().measure_time(name)


def add_metric(name: str, value: Union[float, int], unit: str = "", 
              context: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for adding metrics."""
    get_performance_monitor().add_metric(name, value, unit, context)