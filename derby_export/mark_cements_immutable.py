#!/usr/bin/env python3
"""
Mark all existing cements in the database as immutable.
This preserves the original experimental cements from editing.
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
from app.models.cement import CementUpdate
from sqlalchemy import text

def mark_existing_cements_immutable():
    """Mark all existing cements as immutable."""
    
    # Setup database connection
    db_config = DatabaseConfig("vcctl.db")
    db_service = DatabaseService(db_config)
    cement_service = CementService(db_service)
    
    print("🔒 Marking all existing cements as immutable...")
    print("=" * 50)
    
    try:
        # First, add the immutable column if it doesn't exist
        with db_service.get_session() as session:
            try:
                # Check if column exists
                result = session.execute(text("PRAGMA table_info(cement)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'immutable' not in columns:
                    print("📊 Adding immutable column to database...")
                    session.execute(text("ALTER TABLE cement ADD COLUMN immutable BOOLEAN DEFAULT 0"))
                    session.commit()
                    print("✅ Added immutable column")
                else:
                    print("📊 Immutable column already exists")
                    
            except Exception as e:
                print(f"⚠️ Column addition error (may be expected): {e}")
        
        # Get all cements
        all_cements = cement_service.get_all()
        print(f"📋 Found {len(all_cements)} cements to mark as immutable")
        
        success_count = 0
        for cement in all_cements:
            try:
                # Update cement to be immutable
                update_data = CementUpdate(immutable=True)
                cement_service.update(cement.id, update_data)
                
                print(f"🔒 Marked {cement.name} as immutable")
                success_count += 1
                
            except Exception as e:
                print(f"❌ Failed to update {cement.name}: {e}")
        
        print("=" * 50)
        print(f"✅ Successfully marked {success_count}/{len(all_cements)} cements as immutable")
        print("🎯 All original experimental cements are now protected from editing")
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    mark_existing_cements_immutable()