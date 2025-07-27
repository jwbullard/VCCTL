#!/usr/bin/env python3
"""
Check which cements have phase fractions not totaling 100%
"""

import sqlite3
import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from app.services.cement_service import CementService
from app.database.service import DatabaseService
from app.database.config import DatabaseConfig

def check_phase_fractions():
    # Initialize the database service directly
    db_config = DatabaseConfig("vcctl.db")
    db_service = DatabaseService(db_config)
    cement_service = CementService(db_service)
    
    # Get all cements
    cements = cement_service.get_all()
    
    print("Checking phase fractions for all cements...")
    print("=" * 80)
    
    cements_to_fix = []
    
    for cement in cements:
        # Calculate total phase fractions
        phase_fractions = [
            cement.c3s_mass_fraction or 0.0,
            cement.c2s_mass_fraction or 0.0,
            cement.c3a_mass_fraction or 0.0,
            cement.c4af_mass_fraction or 0.0,
            cement.k2so4_mass_fraction or 0.0,
            cement.na2so4_mass_fraction or 0.0
        ]
        
        total = sum(phase_fractions)
        
        # Check if any phase fractions exist (not all zeros)
        has_phase_data = any(frac > 0 for frac in phase_fractions)
        
        if has_phase_data:
            if abs(total - 1.0) > 0.001:  # Allow small floating point tolerance
                print(f"❌ {cement.name}: Total = {total:.4f} ({total*100:.2f}%)")
                cements_to_fix.append({
                    'cement': cement,
                    'current_total': total,
                    'fractions': phase_fractions
                })
            else:
                print(f"✅ {cement.name}: Total = {total:.4f} ({total*100:.2f}%)")
        else:
            print(f"⚪ {cement.name}: No phase fraction data")
    
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"Total cements: {len(cements)}")
    print(f"Cements needing normalization: {len(cements_to_fix)}")
    
    return cements_to_fix

if __name__ == "__main__":
    cements_to_fix = check_phase_fractions()
    
    if cements_to_fix:
        print(f"\nCements that need fixing:")
        for item in cements_to_fix:
            cement = item['cement']
            print(f"- {cement.name} (total: {item['current_total']:.4f})")