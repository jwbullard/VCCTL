#!/usr/bin/env python3
"""
Check if cements are properly marked as immutable
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

def check_immutable_status():
    """Check immutable status of cements."""
    
    # Setup database connection
    db_config = DatabaseConfig("vcctl.db")
    db_service = DatabaseService(db_config)
    cement_service = CementService(db_service)
    
    print("🔍 Checking immutable status of cements...")
    print("=" * 50)
    
    # Get all cements
    all_cements = cement_service.get_all()
    
    immutable_count = 0
    mutable_count = 0
    
    for cement in all_cements[:10]:  # Check first 10
        cement_dict = cement.to_dict()
        is_immutable = cement_dict.get('immutable', False)
        
        status = "🔒 IMMUTABLE" if is_immutable else "✏️ MUTABLE"
        print(f"{status} - {cement.name}")
        
        if is_immutable:
            immutable_count += 1
        else:
            mutable_count += 1
    
    print("=" * 50)
    print(f"Sample of {len(all_cements)} total cements:")
    print(f"🔒 Immutable: {immutable_count}")
    print(f"✏️ Mutable: {mutable_count}")

if __name__ == "__main__":
    check_immutable_status()