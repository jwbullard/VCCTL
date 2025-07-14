#!/usr/bin/env python3
"""
File History and Versioning for VCCTL

Provides file versioning, history tracking, and backup management
for project files and materials.
"""

import json
import logging
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import shutil


class ChangeType(Enum):
    """Types of file changes."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"


@dataclass
class FileVersion:
    """Represents a version of a file."""
    version_id: str
    timestamp: float
    file_path: str
    backup_path: str
    file_size: int
    file_hash: str
    change_type: ChangeType
    comment: Optional[str] = None
    user: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def datetime(self) -> datetime:
        """Get version timestamp as datetime."""
        return datetime.fromtimestamp(self.timestamp)
    
    @property
    def age_days(self) -> float:
        """Get age of this version in days."""
        return (time.time() - self.timestamp) / (24 * 3600)


@dataclass
class FileHistory:
    """History of all versions of a file."""
    file_path: str
    versions: List[FileVersion] = field(default_factory=list)
    created_timestamp: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    
    @property
    def current_version(self) -> Optional[FileVersion]:
        """Get the most recent version."""
        return self.versions[-1] if self.versions else None
    
    @property
    def version_count(self) -> int:
        """Get total number of versions."""
        return len(self.versions)
    
    def get_version_by_id(self, version_id: str) -> Optional[FileVersion]:
        """Get a specific version by ID."""
        for version in self.versions:
            if version.version_id == version_id:
                return version
        return None
    
    def get_versions_since(self, timestamp: float) -> List[FileVersion]:
        """Get all versions since a specific timestamp."""
        return [v for v in self.versions if v.timestamp >= timestamp]
    
    def get_versions_in_range(self, start: float, end: float) -> List[FileVersion]:
        """Get versions within a time range."""
        return [v for v in self.versions if start <= v.timestamp <= end]


class FileHistoryManager:
    """
    Manages file history and versioning for VCCTL files.
    
    Features:
    - Automatic versioning on file changes
    - Configurable retention policies
    - Backup and restore functionality
    - History browsing and comparison
    - Metadata tracking
    """
    
    def __init__(self, history_directory: Path, max_versions: int = 10,
                 max_age_days: int = 30, max_total_size_mb: int = 100):
        """
        Initialize the file history manager.
        
        Args:
            history_directory: Directory to store version history
            max_versions: Maximum versions to keep per file
            max_age_days: Maximum age of versions in days
            max_total_size_mb: Maximum total size of all backups in MB
        """
        self.history_directory = Path(history_directory)
        self.max_versions = max_versions
        self.max_age_days = max_age_days
        self.max_total_size_mb = max_total_size_mb
        
        self.logger = logging.getLogger('VCCTL.FileHistoryManager')
        
        # Ensure history directory exists
        self.history_directory.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.versions_dir = self.history_directory / "versions"
        self.metadata_dir = self.history_directory / "metadata"
        self.versions_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        
        # Load existing histories
        self.file_histories: Dict[str, FileHistory] = {}
        self._load_histories()
        
        self.logger.info(f"File history manager initialized: {self.history_directory}")
    
    def track_file(self, file_path: Path, change_type: ChangeType = ChangeType.MODIFIED,
                  comment: Optional[str] = None, user: Optional[str] = None) -> str:
        """
        Track a file change and create a new version.
        
        Args:
            file_path: Path to the file to track
            change_type: Type of change
            comment: Optional comment for this version
            user: User who made the change
            
        Returns:
            Version ID of the created version
        """
        try:
            file_path = Path(file_path).resolve()
            file_key = str(file_path)
            
            # Get or create file history
            if file_key not in self.file_histories:
                self.file_histories[file_key] = FileHistory(
                    file_path=file_key,
                    created_timestamp=time.time()
                )
            
            history = self.file_histories[file_key]
            history.last_accessed = time.time()
            
            # Create version
            version_id = self._generate_version_id(file_path)
            
            if file_path.exists() and change_type != ChangeType.DELETED:
                # Calculate file hash
                file_hash = self._calculate_file_hash(file_path)
                
                # Check if file actually changed (unless it's a new file)
                if (change_type != ChangeType.CREATED and history.current_version and 
                    history.current_version.file_hash == file_hash):
                    self.logger.debug(f"File unchanged, skipping version: {file_path}")
                    return history.current_version.version_id
                
                # Create backup
                backup_path = self._create_backup(file_path, version_id)
                file_size = file_path.stat().st_size
            else:
                # File deleted or doesn't exist
                backup_path = ""
                file_size = 0
                file_hash = ""
            
            # Create version record
            version = FileVersion(
                version_id=version_id,
                timestamp=time.time(),
                file_path=file_key,
                backup_path=backup_path,
                file_size=file_size,
                file_hash=file_hash,
                change_type=change_type,
                comment=comment,
                user=user
            )
            
            # Add to history
            history.versions.append(version)
            
            # Apply retention policies
            self._apply_retention_policies(history)
            
            # Save history
            self._save_history(history)
            
            self.logger.info(f"Tracked file change: {file_path} ({change_type.value})")
            return version_id
            
        except Exception as e:
            self.logger.error(f"Failed to track file {file_path}: {e}")
            raise
    
    def restore_version(self, file_path: Path, version_id: str) -> bool:
        """
        Restore a file to a specific version.
        
        Args:
            file_path: Path where to restore the file
            version_id: ID of the version to restore
            
        Returns:
            True if restoration was successful
        """
        try:
            file_key = str(Path(file_path).resolve())
            
            if file_key not in self.file_histories:
                self.logger.error(f"No history found for file: {file_path}")
                return False
            
            history = self.file_histories[file_key]
            version = history.get_version_by_id(version_id)
            
            if not version:
                self.logger.error(f"Version not found: {version_id}")
                return False
            
            if not version.backup_path or not Path(version.backup_path).exists():
                self.logger.error(f"Backup file not found: {version.backup_path}")
                return False
            
            # Create backup of current file before restoring
            if file_path.exists():
                self.track_file(file_path, ChangeType.MODIFIED, 
                              f"Backup before restore to {version_id}")
            
            # Restore the file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(version.backup_path, file_path)
            
            # Track the restoration
            self.track_file(file_path, ChangeType.MODIFIED,
                          f"Restored to version {version_id}")
            
            self.logger.info(f"Restored {file_path} to version {version_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore {file_path} to {version_id}: {e}")
            return False
    
    def get_file_history(self, file_path: Path) -> Optional[FileHistory]:
        """Get the history of a file."""
        file_key = str(Path(file_path).resolve())
        return self.file_histories.get(file_key)
    
    def get_version_content(self, file_path: Path, version_id: str) -> Optional[bytes]:
        """Get the content of a specific version."""
        history = self.get_file_history(file_path)
        if not history:
            return None
        
        version = history.get_version_by_id(version_id)
        if not version or not version.backup_path:
            return None
        
        backup_path = Path(version.backup_path)
        if not backup_path.exists():
            return None
        
        try:
            return backup_path.read_bytes()
        except Exception as e:
            self.logger.error(f"Failed to read version content: {e}")
            return None
    
    def compare_versions(self, file_path: Path, version1_id: str, 
                        version2_id: str) -> Optional[Dict[str, Any]]:
        """
        Compare two versions of a file.
        
        Returns:
            Dictionary with comparison results or None if comparison failed
        """
        history = self.get_file_history(file_path)
        if not history:
            return None
        
        version1 = history.get_version_by_id(version1_id)
        version2 = history.get_version_by_id(version2_id)
        
        if not version1 or not version2:
            return None
        
        comparison = {
            'version1': {
                'id': version1.version_id,
                'timestamp': version1.timestamp,
                'datetime': version1.datetime.isoformat(),
                'size': version1.file_size,
                'hash': version1.file_hash,
                'comment': version1.comment
            },
            'version2': {
                'id': version2.version_id,
                'timestamp': version2.timestamp,
                'datetime': version2.datetime.isoformat(),
                'size': version2.file_size,
                'hash': version2.file_hash,
                'comment': version2.comment
            },
            'size_change': version2.file_size - version1.file_size,
            'time_difference': version2.timestamp - version1.timestamp,
            'content_changed': version1.file_hash != version2.file_hash
        }
        
        return comparison
    
    def cleanup_history(self, file_path: Optional[Path] = None) -> Dict[str, int]:
        """
        Clean up history based on retention policies.
        
        Args:
            file_path: Specific file to clean up (None for all files)
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            'files_processed': 0,
            'versions_removed': 0,
            'bytes_freed': 0
        }
        
        try:
            if file_path:
                # Clean up specific file
                file_key = str(Path(file_path).resolve())
                if file_key in self.file_histories:
                    history = self.file_histories[file_key]
                    removed = self._apply_retention_policies(history)
                    stats['files_processed'] = 1
                    stats['versions_removed'] = removed
            else:
                # Clean up all files
                for history in self.file_histories.values():
                    removed = self._apply_retention_policies(history)
                    stats['files_processed'] += 1
                    stats['versions_removed'] += removed
                
                # Apply global size limit
                self._apply_global_size_limit()
            
            # Calculate freed space (approximation)
            stats['bytes_freed'] = stats['versions_removed'] * 1024  # Rough estimate
            
            self.logger.info(f"Cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return stats
    
    def export_history(self, output_path: Path, 
                      file_paths: Optional[List[Path]] = None) -> bool:
        """
        Export file histories to a JSON file.
        
        Args:
            output_path: Path for the export file
            file_paths: Specific files to export (None for all)
            
        Returns:
            True if export was successful
        """
        try:
            export_data = {
                'export_timestamp': time.time(),
                'export_datetime': datetime.now().isoformat(),
                'histories': {}
            }
            
            if file_paths:
                # Export specific files
                for file_path in file_paths:
                    file_key = str(Path(file_path).resolve())
                    if file_key in self.file_histories:
                        export_data['histories'][file_key] = asdict(self.file_histories[file_key])
            else:
                # Export all histories
                for file_key, history in self.file_histories.items():
                    export_data['histories'][file_key] = asdict(history)
            
            # Write export file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported {len(export_data['histories'])} histories to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the file history system."""
        total_versions = 0
        total_size = 0
        oldest_timestamp = float('inf')
        newest_timestamp = 0
        
        for history in self.file_histories.values():
            total_versions += len(history.versions)
            for version in history.versions:
                total_size += version.file_size
                oldest_timestamp = min(oldest_timestamp, version.timestamp)
                newest_timestamp = max(newest_timestamp, version.timestamp)
        
        if oldest_timestamp == float('inf'):
            oldest_timestamp = 0
        
        return {
            'tracked_files': len(self.file_histories),
            'total_versions': total_versions,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_version': datetime.fromtimestamp(oldest_timestamp).isoformat() if oldest_timestamp else None,
            'newest_version': datetime.fromtimestamp(newest_timestamp).isoformat() if newest_timestamp else None,
            'average_versions_per_file': total_versions / len(self.file_histories) if self.file_histories else 0
        }
    
    def _generate_version_id(self, file_path: Path) -> str:
        """Generate a unique version ID."""
        timestamp = str(int(time.time() * 1000000))  # Microsecond precision
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
        return f"{timestamp}_{file_hash}"
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def _create_backup(self, file_path: Path, version_id: str) -> str:
        """Create a backup copy of the file."""
        # Create backup filename with version ID
        suffix = file_path.suffix
        backup_name = f"{version_id}{suffix}"
        backup_path = self.versions_dir / backup_name
        
        # Copy file to backup location
        shutil.copy2(file_path, backup_path)
        
        return str(backup_path)
    
    def _apply_retention_policies(self, history: FileHistory) -> int:
        """Apply retention policies to a file history."""
        removed_count = 0
        current_time = time.time()
        
        # Sort versions by timestamp (oldest first)
        history.versions.sort(key=lambda v: v.timestamp)
        
        versions_to_remove = []
        
        # Apply age-based retention
        if self.max_age_days > 0:
            cutoff_time = current_time - (self.max_age_days * 24 * 3600)
            for version in history.versions[:-1]:  # Keep at least the latest version
                if version.timestamp < cutoff_time:
                    versions_to_remove.append(version)
        
        # Apply count-based retention
        if len(history.versions) > self.max_versions:
            excess_count = len(history.versions) - self.max_versions
            # Remove oldest versions first, but keep the latest one
            for version in history.versions[:excess_count]:
                if version not in versions_to_remove:
                    versions_to_remove.append(version)
        
        # Remove versions
        for version in versions_to_remove:
            try:
                # Remove backup file
                if version.backup_path and Path(version.backup_path).exists():
                    Path(version.backup_path).unlink()
                
                # Remove from history
                history.versions.remove(version)
                removed_count += 1
                
            except Exception as e:
                self.logger.warning(f"Failed to remove version {version.version_id}: {e}")
        
        return removed_count
    
    def _apply_global_size_limit(self) -> None:
        """Apply global size limit across all histories."""
        if self.max_total_size_mb <= 0:
            return
        
        max_size_bytes = self.max_total_size_mb * 1024 * 1024
        
        # Calculate current total size
        total_size = 0
        all_versions = []
        
        for history in self.file_histories.values():
            for version in history.versions:
                total_size += version.file_size
                all_versions.append((version, history))
        
        if total_size <= max_size_bytes:
            return
        
        # Sort by timestamp (oldest first)
        all_versions.sort(key=lambda x: x[0].timestamp)
        
        # Remove oldest versions until under limit
        for version, history in all_versions:
            if total_size <= max_size_bytes:
                break
            
            # Don't remove the latest version of any file
            if version == history.current_version:
                continue
            
            try:
                # Remove backup file
                if version.backup_path and Path(version.backup_path).exists():
                    Path(version.backup_path).unlink()
                
                # Remove from history
                history.versions.remove(version)
                total_size -= version.file_size
                
            except Exception as e:
                self.logger.warning(f"Failed to remove version {version.version_id}: {e}")
    
    def _load_histories(self) -> None:
        """Load existing file histories from disk."""
        try:
            for metadata_file in self.metadata_dir.glob("*.json"):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Convert data back to FileHistory object
                    history = FileHistory(
                        file_path=data['file_path'],
                        created_timestamp=data.get('created_timestamp', time.time()),
                        last_accessed=data.get('last_accessed', time.time())
                    )
                    
                    # Convert version data
                    for version_data in data.get('versions', []):
                        version = FileVersion(
                            version_id=version_data['version_id'],
                            timestamp=version_data['timestamp'],
                            file_path=version_data['file_path'],
                            backup_path=version_data['backup_path'],
                            file_size=version_data['file_size'],
                            file_hash=version_data['file_hash'],
                            change_type=ChangeType(version_data['change_type']),
                            comment=version_data.get('comment'),
                            user=version_data.get('user'),
                            metadata=version_data.get('metadata', {})
                        )
                        history.versions.append(version)
                    
                    self.file_histories[history.file_path] = history
                    
                except Exception as e:
                    self.logger.warning(f"Failed to load history from {metadata_file}: {e}")
            
            self.logger.info(f"Loaded {len(self.file_histories)} file histories")
            
        except Exception as e:
            self.logger.error(f"Failed to load histories: {e}")
    
    def _save_history(self, history: FileHistory) -> None:
        """Save a file history to disk."""
        try:
            # Create metadata filename based on file path hash
            file_hash = hashlib.md5(history.file_path.encode()).hexdigest()
            metadata_file = self.metadata_dir / f"{file_hash}.json"
            
            # Convert to serializable format
            data = asdict(history)
            
            # Write metadata file
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save history for {history.file_path}: {e}")
    
    def __del__(self):
        """Cleanup when manager is destroyed."""
        try:
            # Save all histories
            for history in self.file_histories.values():
                self._save_history(history)
        except:
            pass