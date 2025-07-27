#!/usr/bin/env python3
"""
Retry importing the failed PSD data (ma160, ma157, sacement)
"""

import json
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

def retry_failed_imports():
    """Retry importing the cements that failed due to size limits."""
    
    # The cements that failed in the previous run
    failed_cements = ['ma160', 'ma157', 'sacement']
    
    # First, let's extract their PSD data again
    from import_psd_data import extract_psd_data_from_csv
    
    csv_file = Path(__file__).parent / "psd_data.csv"
    psd_data = extract_psd_data_from_csv(csv_file)
    
    # Setup database connection
    db_config = DatabaseConfig("vcctl.db")
    db_service = DatabaseService(db_config)
    cement_service = CementService(db_service)
    
    print("🔄 Retrying failed PSD imports after model update...")
    print("=" * 50)
    
    for cement_name in failed_cements:
        if cement_name in psd_data:
            cement = cement_service.get_by_name(cement_name)
            if cement:
                try:
                    psd_points = psd_data[cement_name]
                    psd_json = json.dumps(psd_points)
                    
                    print(f"📏 {cement_name}: {len(psd_points)} points, {len(psd_json)} characters")
                    
                    update_data = CementUpdate(
                        psd_custom_points=psd_json,
                        psd_mode='custom'
                    )
                    
                    cement_service.update(cement.id, update_data)
                    print(f"✅ Successfully updated {cement_name}")
                    
                except Exception as e:
                    print(f"❌ Still failed for {cement_name}: {e}")
            else:
                print(f"⚠️ {cement_name} not found in database")
        else:
            print(f"⚠️ No PSD data found for {cement_name}")

if __name__ == "__main__":
    retry_failed_imports()