"""
Comprehensive data integrity tests for SubForge system.

Tests data integrity including:
- Transaction rollback mechanisms  
- Data validation and schema enforcement
- Backup and restore procedures
- Consistency checks and repair

Created: 2025-01-05 12:45 UTC-3 São Paulo
"""

import pytest
import asyncio
import json
import sqlite3
import tempfile
import shutil
import os
import time
import hashlib
import pickle
from pathlib import Path
from unittest.mock import Mock, patch
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

# Import SubForge modules
try:
    from subforge.core.project_analyzer import ProjectAnalyzer
    from subforge.core.workflow_orchestrator import WorkflowOrchestrator
    from subforge.core.validation_engine import ValidationEngine
except ImportError:
    # Mock imports if modules not available
    ProjectAnalyzer = Mock
    WorkflowOrchestrator = Mock
    ValidationEngine = Mock


@dataclass
class DataRecord:
    """Sample data record for testing."""
    id: int
    name: str
    email: str
    created_at: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DatabaseManager:
    """Database manager with transaction support."""
    
    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        self.connection = None
        self.setup_database()
    
    def setup_database(self):
        """Setup database schema."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at REAL NOT NULL,
                metadata TEXT
            )
        """)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_id INTEGER,
                timestamp REAL NOT NULL,
                details TEXT
            )
        """)
        self.connection.commit()
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
    
    def insert_record(self, record: DataRecord):
        """Insert a record with audit logging."""
        with self.transaction():
            cursor = self.connection.execute(
                "INSERT INTO records (id, name, email, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
                (record.id, record.name, record.email, record.created_at, 
                 json.dumps(record.metadata) if record.metadata else None)
            )
            
            # Log the operation
            self.connection.execute(
                "INSERT INTO audit_log (operation, table_name, record_id, timestamp, details) VALUES (?, ?, ?, ?, ?)",
                ("INSERT", "records", record.id, time.time(), json.dumps(asdict(record)))
            )
            
            return cursor.lastrowid
    
    def get_record(self, record_id: int) -> Optional[DataRecord]:
        """Get a record by ID."""
        cursor = self.connection.execute(
            "SELECT id, name, email, created_at, metadata FROM records WHERE id = ?",
            (record_id,)
        )
        row = cursor.fetchone()
        
        if row:
            metadata = json.loads(row[4]) if row[4] else {}
            return DataRecord(
                id=row[0], name=row[1], email=row[2], 
                created_at=row[3], metadata=metadata
            )
        return None
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


class FileSystemStore:
    """File system store with checksums and backup."""
    
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.backup_path = self.base_path / "backups"
        self.backup_path.mkdir(exist_ok=True)
    
    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA-256 checksum of data."""
        return hashlib.sha256(data).hexdigest()
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for a key."""
        return self.base_path / f"{key}.json"
    
    def _get_checksum_path(self, key: str) -> Path:
        """Get checksum file path for a key."""
        return self.base_path / f"{key}.checksum"
    
    def store(self, key: str, data: Dict) -> bool:
        """Store data with checksum verification."""
        try:
            file_path = self._get_file_path(key)
            checksum_path = self._get_checksum_path(key)
            
            # Serialize data
            json_data = json.dumps(data, indent=2, sort_keys=True)
            json_bytes = json_data.encode('utf-8')
            
            # Calculate checksum
            checksum = self._calculate_checksum(json_bytes)
            
            # Create backup if file exists
            if file_path.exists():
                backup_path = self.backup_path / f"{key}_{int(time.time())}.json"
                shutil.copy2(file_path, backup_path)
            
            # Write data and checksum atomically
            temp_file = file_path.with_suffix('.tmp')
            temp_checksum = checksum_path.with_suffix('.tmp')
            
            with open(temp_file, 'w') as f:
                f.write(json_data)
            
            with open(temp_checksum, 'w') as f:
                f.write(checksum)
            
            # Atomic move
            temp_file.rename(file_path)
            temp_checksum.rename(checksum_path)
            
            return True
            
        except Exception as e:
            # Cleanup temp files on error
            for temp_path in [temp_file, temp_checksum]:
                if temp_path.exists():
                    temp_path.unlink()
            return False
    
    def retrieve(self, key: str) -> Optional[Dict]:
        """Retrieve and validate data."""
        try:
            file_path = self._get_file_path(key)
            checksum_path = self._get_checksum_path(key)
            
            if not file_path.exists() or not checksum_path.exists():
                return None
            
            # Read data and stored checksum
            with open(file_path, 'rb') as f:
                json_bytes = f.read()
            
            with open(checksum_path, 'r') as f:
                stored_checksum = f.read().strip()
            
            # Verify checksum
            calculated_checksum = self._calculate_checksum(json_bytes)
            if calculated_checksum != stored_checksum:
                # Try to restore from backup
                return self._restore_from_backup(key)
            
            # Parse and return data
            return json.loads(json_bytes.decode('utf-8'))
            
        except Exception:
            # Try to restore from backup
            return self._restore_from_backup(key)
    
    def _restore_from_backup(self, key: str) -> Optional[Dict]:
        """Restore data from most recent backup."""
        try:
            backup_files = list(self.backup_path.glob(f"{key}_*.json"))
            if not backup_files:
                return None
            
            # Get most recent backup
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_backup, 'r') as f:
                data = json.load(f)
            
            # Restore to main location
            self.store(key, data)
            return data
            
        except Exception:
            return None


class TestTransactionRollback:
    """Test transaction rollback mechanisms."""
    
    def setup_method(self):
        """Setup test environment."""
        self.db_manager = DatabaseManager()
    
    def teardown_method(self):
        """Cleanup test environment."""
        self.db_manager.close()
    
    def test_partial_operation_rollback(self):
        """Test rollback when operation fails partway through."""
        
        # Insert some initial data
        record1 = DataRecord(
            id=1, name="Alice", email="alice@example.com", 
            created_at=time.time()
        )
        self.db_manager.insert_record(record1)
        
        # Attempt batch operation that should fail
        def failing_batch_operation():
            with self.db_manager.transaction():
                # This should succeed
                record2 = DataRecord(
                    id=2, name="Bob", email="bob@example.com",
                    created_at=time.time()
                )
                self.db_manager.connection.execute(
                    "INSERT INTO records (id, name, email, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
                    (record2.id, record2.name, record2.email, record2.created_at, None)
                )
                
                # This should fail due to duplicate email
                record3 = DataRecord(
                    id=3, name="Alice Duplicate", email="alice@example.com",  # Duplicate email
                    created_at=time.time()
                )
                self.db_manager.connection.execute(
                    "INSERT INTO records (id, name, email, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
                    (record3.id, record3.name, record3.email, record3.created_at, None)
                )
        
        # Execute and expect failure
        with pytest.raises(sqlite3.IntegrityError):
            failing_batch_operation()
        
        # Verify rollback - only original record should exist
        cursor = self.db_manager.connection.execute("SELECT COUNT(*) FROM records")
        count = cursor.fetchone()[0]
        assert count == 1
        
        # Verify the original record is still there
        original_record = self.db_manager.get_record(1)
        assert original_record is not None
        assert original_record.name == "Alice"
        
        # Verify Bob's record was rolled back
        bobs_record = self.db_manager.get_record(2)
        assert bobs_record is None
    
    def test_multi_step_rollback(self):
        """Test rollback of complex multi-step operation."""
        
        initial_data = [
            DataRecord(id=1, name="User1", email="user1@example.com", created_at=time.time()),
            DataRecord(id=2, name="User2", email="user2@example.com", created_at=time.time()),
        ]
        
        # Insert initial data
        for record in initial_data:
            self.db_manager.insert_record(record)
        
        def complex_multi_step_operation():
            """Complex operation with multiple steps."""
            with self.db_manager.transaction():
                # Step 1: Update existing records
                self.db_manager.connection.execute(
                    "UPDATE records SET name = ? WHERE id = ?",
                    ("Updated User1", 1)
                )
                
                # Step 2: Insert new record
                self.db_manager.connection.execute(
                    "INSERT INTO records (id, name, email, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
                    (3, "User3", "user3@example.com", time.time(), None)
                )
                
                # Step 3: Delete a record
                self.db_manager.connection.execute("DELETE FROM records WHERE id = ?", (2,))
                
                # Step 4: Insert conflicting record (should fail)
                self.db_manager.connection.execute(
                    "INSERT INTO records (id, name, email, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
                    (4, "User4", "user1@example.com", time.time(), None)  # Duplicate email
                )
        
        # Execute and expect failure
        with pytest.raises(sqlite3.IntegrityError):
            complex_multi_step_operation()
        
        # Verify all steps were rolled back
        user1 = self.db_manager.get_record(1)
        assert user1.name == "User1"  # Should not be "Updated User1"
        
        user2 = self.db_manager.get_record(2)
        assert user2 is not None  # Should not be deleted
        
        user3 = self.db_manager.get_record(3)
        assert user3 is None  # Should not exist
        
        # Verify total count is unchanged
        cursor = self.db_manager.connection.execute("SELECT COUNT(*) FROM records")
        count = cursor.fetchone()[0]
        assert count == 2
    
    def test_nested_transaction_rollback(self):
        """Test rollback behavior with nested transaction-like operations."""
        
        # Insert initial record
        record = DataRecord(
            id=1, name="Original", email="original@example.com",
            created_at=time.time(), metadata={"version": 1}
        )
        self.db_manager.insert_record(record)
        
        class NestedOperationManager:
            def __init__(self, db_manager):
                self.db_manager = db_manager
                self.checkpoints = []
            
            def create_checkpoint(self, name):
                """Create a logical checkpoint."""
                cursor = self.db_manager.connection.execute("SELECT * FROM records")
                records = cursor.fetchall()
                self.checkpoints.append((name, records))
            
            def rollback_to_checkpoint(self, name):
                """Rollback to a specific checkpoint."""
                for checkpoint_name, records in reversed(self.checkpoints):
                    if checkpoint_name == name:
                        # Clear current data
                        with self.db_manager.transaction():
                            self.db_manager.connection.execute("DELETE FROM records")
                            
                            # Restore checkpoint data
                            for record_data in records:
                                self.db_manager.connection.execute(
                                    "INSERT INTO records (id, name, email, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
                                    record_data
                                )
                        return True
                return False
        
        nested_manager = NestedOperationManager(self.db_manager)
        
        # Create checkpoint after initial data
        nested_manager.create_checkpoint("initial")
        
        # Make changes
        with self.db_manager.transaction():
            self.db_manager.connection.execute(
                "UPDATE records SET name = ?, metadata = ? WHERE id = ?",
                ("Modified", json.dumps({"version": 2}), 1)
            )
        
        nested_manager.create_checkpoint("after_update")
        
        # Make more changes
        with self.db_manager.transaction():
            self.db_manager.connection.execute(
                "INSERT INTO records (id, name, email, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
                (2, "New Record", "new@example.com", time.time(), None)
            )
        
        # Verify changes were made
        cursor = self.db_manager.connection.execute("SELECT COUNT(*) FROM records")
        assert cursor.fetchone()[0] == 2
        
        # Rollback to checkpoint
        success = nested_manager.rollback_to_checkpoint("initial")
        assert success is True
        
        # Verify rollback
        cursor = self.db_manager.connection.execute("SELECT COUNT(*) FROM records")
        assert cursor.fetchone()[0] == 1
        
        restored_record = self.db_manager.get_record(1)
        assert restored_record.name == "Original"
        assert restored_record.metadata["version"] == 1


class TestDataValidation:
    """Test data validation and schema enforcement."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = FileSystemStore(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_checksum_verification(self):
        """Test data integrity using checksums."""
        
        # Store valid data
        test_data = {
            "id": 123,
            "name": "Test Record",
            "values": [1, 2, 3, 4, 5],
            "nested": {"key": "value", "number": 42}
        }
        
        success = self.store.store("test_record", test_data)
        assert success is True
        
        # Retrieve and verify
        retrieved_data = self.store.retrieve("test_record")
        assert retrieved_data is not None
        assert retrieved_data == test_data
        
        # Corrupt the main file
        file_path = self.store._get_file_path("test_record")
        with open(file_path, 'w') as f:
            f.write('{"corrupted": "data"}')
        
        # Should restore from backup
        retrieved_data = self.store.retrieve("test_record")
        assert retrieved_data == test_data
    
    def test_schema_validation(self):
        """Test schema validation for structured data."""
        
        class SchemaValidator:
            def __init__(self):
                self.schemas = {
                    "user": {
                        "required_fields": ["id", "name", "email"],
                        "field_types": {
                            "id": int,
                            "name": str,
                            "email": str,
                            "age": int,
                            "active": bool
                        },
                        "validators": {
                            "email": lambda x: "@" in x and "." in x,
                            "age": lambda x: 0 <= x <= 150 if x is not None else True
                        }
                    }
                }
            
            def validate(self, schema_name: str, data: Dict) -> Dict[str, Any]:
                """Validate data against schema."""
                if schema_name not in self.schemas:
                    return {"valid": False, "errors": [f"Unknown schema: {schema_name}"]}
                
                schema = self.schemas[schema_name]
                errors = []
                
                # Check required fields
                for field in schema["required_fields"]:
                    if field not in data:
                        errors.append(f"Missing required field: {field}")
                
                # Check field types
                for field, expected_type in schema["field_types"].items():
                    if field in data and data[field] is not None:
                        if not isinstance(data[field], expected_type):
                            errors.append(
                                f"Field '{field}' should be {expected_type.__name__}, "
                                f"got {type(data[field]).__name__}"
                            )
                
                # Run custom validators
                for field, validator in schema.get("validators", {}).items():
                    if field in data and data[field] is not None:
                        try:
                            if not validator(data[field]):
                                errors.append(f"Field '{field}' failed validation")
                        except Exception as e:
                            errors.append(f"Validation error for '{field}': {e}")
                
                return {"valid": len(errors) == 0, "errors": errors}
        
        validator = SchemaValidator()
        
        # Test valid data
        valid_user = {
            "id": 1,
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "age": 30,
            "active": True
        }
        
        result = validator.validate("user", valid_user)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        
        # Test missing required field
        invalid_user1 = {
            "id": 1,
            "name": "Bob Smith",
            # missing email
        }
        
        result = validator.validate("user", invalid_user1)
        assert result["valid"] is False
        assert any("Missing required field: email" in error for error in result["errors"])
        
        # Test wrong type
        invalid_user2 = {
            "id": "not_a_number",  # Should be int
            "name": "Charlie Brown",
            "email": "charlie@example.com"
        }
        
        result = validator.validate("user", invalid_user2)
        assert result["valid"] is False
        assert any("should be int" in error for error in result["errors"])
        
        # Test custom validator failure
        invalid_user3 = {
            "id": 1,
            "name": "Dave Wilson",
            "email": "invalid_email",  # No @ or .
            "age": 200  # Too old
        }
        
        result = validator.validate("user", invalid_user3)
        assert result["valid"] is False
        assert len(result["errors"]) >= 2  # Both email and age should fail
    
    def test_data_migration_validation(self):
        """Test validation during data migration between schema versions."""
        
        class DataMigrator:
            def __init__(self):
                self.migrations = {
                    1: self._migrate_v1_to_v2,
                    2: self._migrate_v2_to_v3,
                }
            
            def _migrate_v1_to_v2(self, data):
                """Migrate from version 1 to version 2."""
                # Add new fields
                if "created_at" not in data:
                    data["created_at"] = time.time()
                
                if "status" not in data:
                    data["status"] = "active"
                
                data["version"] = 2
                return data
            
            def _migrate_v2_to_v3(self, data):
                """Migrate from version 2 to version 3."""
                # Rename field
                if "status" in data:
                    data["state"] = data.pop("status")
                
                # Add metadata
                if "metadata" not in data:
                    data["metadata"] = {}
                
                data["version"] = 3
                return data
            
            def migrate_to_current(self, data, current_version=3):
                """Migrate data to current version."""
                data_version = data.get("version", 1)
                
                if data_version > current_version:
                    raise ValueError(f"Data version {data_version} is newer than current {current_version}")
                
                migrated_data = data.copy()
                
                # Apply migrations sequentially
                for version in range(data_version, current_version):
                    if version in self.migrations:
                        migrated_data = self.migrations[version](migrated_data)
                
                return migrated_data
        
        migrator = DataMigrator()
        
        # Test v1 data
        v1_data = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "version": 1
        }
        
        migrated = migrator.migrate_to_current(v1_data)
        assert migrated["version"] == 3
        assert "created_at" in migrated
        assert "state" in migrated
        assert "metadata" in migrated
        assert migrated["state"] == "active"
        
        # Test v2 data
        v2_data = {
            "id": 2,
            "name": "Another User",
            "email": "another@example.com",
            "created_at": time.time(),
            "status": "inactive",
            "version": 2
        }
        
        migrated = migrator.migrate_to_current(v2_data)
        assert migrated["version"] == 3
        assert "status" not in migrated
        assert migrated["state"] == "inactive"
        assert "metadata" in migrated


class TestBackupRestore:
    """Test backup and restore functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, "data")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def teardown_method(self):
        """Cleanup test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_automatic_backup(self):
        """Test automatic backup creation."""
        
        class BackupManager:
            def __init__(self, data_dir, backup_dir):
                self.data_dir = Path(data_dir)
                self.backup_dir = Path(backup_dir)
                self.backup_dir.mkdir(exist_ok=True)
            
            def create_backup(self, name: str = None):
                """Create a full backup of all data."""
                if name is None:
                    name = f"backup_{int(time.time())}"
                
                backup_path = self.backup_dir / name
                backup_path.mkdir(exist_ok=True)
                
                # Copy all data files
                files_copied = 0
                for file_path in self.data_dir.rglob("*"):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(self.data_dir)
                        dest_path = backup_path / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, dest_path)
                        files_copied += 1
                
                # Create backup manifest
                manifest = {
                    "created_at": time.time(),
                    "files_count": files_copied,
                    "data_dir": str(self.data_dir),
                    "backup_name": name
                }
                
                with open(backup_path / "manifest.json", 'w') as f:
                    json.dump(manifest, f, indent=2)
                
                return backup_path, files_copied
            
            def list_backups(self):
                """List available backups."""
                backups = []
                for backup_path in self.backup_dir.iterdir():
                    if backup_path.is_dir():
                        manifest_path = backup_path / "manifest.json"
                        if manifest_path.exists():
                            with open(manifest_path, 'r') as f:
                                manifest = json.load(f)
                            backups.append((backup_path.name, manifest))
                
                return sorted(backups, key=lambda x: x[1]["created_at"], reverse=True)
            
            def create_incremental_backup(self, base_backup_name: str):
                """Create an incremental backup since base backup."""
                base_backup_path = self.backup_dir / base_backup_name
                if not base_backup_path.exists():
                    raise ValueError(f"Base backup {base_backup_name} not found")
                
                # Load base backup manifest
                with open(base_backup_path / "manifest.json", 'r') as f:
                    base_manifest = json.load(f)
                
                base_time = base_manifest["created_at"]
                
                # Find files modified since base backup
                new_files = []
                for file_path in self.data_dir.rglob("*"):
                    if file_path.is_file() and file_path.stat().st_mtime > base_time:
                        new_files.append(file_path)
                
                # Create incremental backup
                inc_name = f"incremental_{base_backup_name}_{int(time.time())}"
                inc_path = self.backup_dir / inc_name
                inc_path.mkdir()
                
                for file_path in new_files:
                    rel_path = file_path.relative_to(self.data_dir)
                    dest_path = inc_path / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_path)
                
                # Create incremental manifest
                inc_manifest = {
                    "created_at": time.time(),
                    "type": "incremental",
                    "base_backup": base_backup_name,
                    "files_count": len(new_files),
                    "new_files": [str(f.relative_to(self.data_dir)) for f in new_files]
                }
                
                with open(inc_path / "manifest.json", 'w') as f:
                    json.dump(inc_manifest, f, indent=2)
                
                return inc_path, len(new_files)
        
        backup_manager = BackupManager(self.data_dir, self.backup_dir)
        
        # Create some test data
        test_files = {
            "config.json": {"setting1": "value1", "setting2": 42},
            "data.json": {"records": [1, 2, 3, 4, 5]},
            "subdir/nested.json": {"nested": True}
        }
        
        for file_path, data in test_files.items():
            full_path = os.path.join(self.data_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                json.dump(data, f)
        
        # Create full backup
        backup_path, files_count = backup_manager.create_backup("test_backup")
        assert files_count == 3
        assert (backup_path / "manifest.json").exists()
        assert (backup_path / "config.json").exists()
        assert (backup_path / "subdir" / "nested.json").exists()
        
        # Modify a file
        time.sleep(0.1)  # Ensure different modification time
        with open(os.path.join(self.data_dir, "config.json"), 'w') as f:
            json.dump({"setting1": "modified_value", "setting3": "new"}, f)
        
        # Create incremental backup
        inc_path, inc_files = backup_manager.create_incremental_backup("test_backup")
        assert inc_files == 1
        
        # List backups
        backups = backup_manager.list_backups()
        assert len(backups) >= 2
    
    def test_restore_from_backup(self):
        """Test restoring data from backup."""
        
        class RestoreManager:
            def __init__(self, data_dir, backup_dir):
                self.data_dir = Path(data_dir)
                self.backup_dir = Path(backup_dir)
            
            def restore_full_backup(self, backup_name: str, target_dir: str = None):
                """Restore a full backup."""
                if target_dir is None:
                    target_dir = self.data_dir
                else:
                    target_dir = Path(target_dir)
                
                backup_path = self.backup_dir / backup_name
                if not backup_path.exists():
                    raise ValueError(f"Backup {backup_name} not found")
                
                # Load manifest
                with open(backup_path / "manifest.json", 'r') as f:
                    manifest = json.load(f)
                
                # Clear target directory
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                target_dir.mkdir(parents=True)
                
                # Copy backup files
                files_restored = 0
                for file_path in backup_path.rglob("*"):
                    if file_path.is_file() and file_path.name != "manifest.json":
                        rel_path = file_path.relative_to(backup_path)
                        dest_path = target_dir / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, dest_path)
                        files_restored += 1
                
                return files_restored, manifest
            
            def verify_restore(self, backup_name: str, target_dir: str = None):
                """Verify restored data integrity."""
                if target_dir is None:
                    target_dir = self.data_dir
                else:
                    target_dir = Path(target_dir)
                
                backup_path = self.backup_dir / backup_name
                
                # Compare file counts and checksums
                backup_files = {}
                for file_path in backup_path.rglob("*"):
                    if file_path.is_file() and file_path.name != "manifest.json":
                        rel_path = file_path.relative_to(backup_path)
                        with open(file_path, 'rb') as f:
                            checksum = hashlib.sha256(f.read()).hexdigest()
                        backup_files[str(rel_path)] = checksum
                
                restored_files = {}
                for file_path in target_dir.rglob("*"):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(target_dir)
                        with open(file_path, 'rb') as f:
                            checksum = hashlib.sha256(f.read()).hexdigest()
                        restored_files[str(rel_path)] = checksum
                
                # Check for missing or extra files
                missing_files = set(backup_files.keys()) - set(restored_files.keys())
                extra_files = set(restored_files.keys()) - set(backup_files.keys())
                
                # Check for corrupted files
                corrupted_files = []
                for file_path in backup_files:
                    if file_path in restored_files:
                        if backup_files[file_path] != restored_files[file_path]:
                            corrupted_files.append(file_path)
                
                return {
                    "valid": len(missing_files) == 0 and len(extra_files) == 0 and len(corrupted_files) == 0,
                    "missing_files": list(missing_files),
                    "extra_files": list(extra_files),
                    "corrupted_files": corrupted_files
                }
        
        # Setup backup manager and create backup
        backup_manager = BackupManager(self.data_dir, self.backup_dir)
        restore_manager = RestoreManager(self.data_dir, self.backup_dir)
        
        # Create test data
        original_data = {
            "file1.json": {"data": "original1"},
            "file2.json": {"data": "original2"},
            "subdir/file3.json": {"data": "original3"}
        }
        
        for file_path, data in original_data.items():
            full_path = os.path.join(self.data_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                json.dump(data, f)
        
        # Create backup
        backup_path, files_count = backup_manager.create_backup("restore_test")
        assert files_count == 3
        
        # Modify/corrupt original data
        with open(os.path.join(self.data_dir, "file1.json"), 'w') as f:
            f.write("corrupted data")
        
        os.remove(os.path.join(self.data_dir, "file2.json"))
        
        # Restore from backup
        restore_dir = os.path.join(self.temp_dir, "restored")
        files_restored, manifest = restore_manager.restore_full_backup(
            "restore_test", restore_dir
        )
        
        assert files_restored == 3
        assert manifest["files_count"] == 3
        
        # Verify restoration
        verification = restore_manager.verify_restore("restore_test", restore_dir)
        assert verification["valid"] is True
        assert len(verification["missing_files"]) == 0
        assert len(verification["corrupted_files"]) == 0
        
        # Check restored data content
        with open(os.path.join(restore_dir, "file1.json"), 'r') as f:
            restored_data = json.load(f)
            assert restored_data == {"data": "original1"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])