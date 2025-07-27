#!/usr/bin/env python3
"""
Test if immutable field is included in to_dict output
"""

from pathlib import Path
import sys

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from app.database.config import DatabaseConfig
from app.database.service import DatabaseService
from app.services.cement_service import CementService

def test_to_dict():
    """Test to_dict output for immutable field."""
    
    # Setup database connection
    db_config = DatabaseConfig("vcctl.db")
    db_service = DatabaseService(db_config)
    cement_service = CementService(db_service)
    
    print("🔍 Testing to_dict() output for immutable field...")
    print("=" * 50)
    
    # Get cement141
    cement = cement_service.get_by_name('cement141')
    data = cement.to_dict()
    
    print(f"Cement: {cement.name}")
    print(f"Immutable field present: {'immutable' in data}")
    print(f"Immutable value: {data.get('immutable')}")
    print(f"Total fields: {len(data)}")
    
    # Show fields containing 'mut'
    mut_fields = [k for k in data.keys() if 'mut' in k.lower()]
    print(f"Fields with 'mut': {mut_fields}")
    
    # Show last 10 fields (immutable should be near the end)
    all_keys = list(data.keys())
    print(f"Last 10 fields: {all_keys[-10:]}")

if __name__ == "__main__":
    test_to_dict()