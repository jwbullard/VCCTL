#!/usr/bin/env python3
"""
Debug cement136 display values
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

def debug_cement136_display():
    # Get cement136 data
    db_config = DatabaseConfig("vcctl.db")
    db_service = DatabaseService(db_config)
    cement_service = CementService(db_service)

    cement = cement_service.get_by_name('cement136')
    if not cement:
        print("Cement136 not found!")
        return

    print(f"Cement: {cement.name}")
    print("\nDatabase fractions (0-1):")
    
    phases = {
        'C3S': cement.c3s_mass_fraction,
        'C2S': cement.c2s_mass_fraction,
        'C3A': cement.c3a_mass_fraction,
        'C4AF': cement.c4af_mass_fraction,
        'K2SO4': cement.k2so4_mass_fraction,
        'Na2SO4': cement.na2so4_mass_fraction
    }
    
    total_fraction = 0.0
    total_percentage = 0.0
    
    for phase, fraction in phases.items():
        if fraction:
            percentage = float(fraction) * 100.0
            print(f"{phase}: {fraction:.15f} -> {percentage:.15f}%")
            total_fraction += fraction
            total_percentage += percentage
        else:
            print(f"{phase}: 0.0 -> 0.0%")
    
    print(f"\nTotals:")
    print(f"Database total (fractions): {total_fraction:.15f}")
    print(f"UI total (percentages): {total_percentage:.15f}")
    print(f"Database total as %: {total_fraction * 100:.15f}")
    
    # Show what rounded display values would be
    print(f"\nRounded display values (as shown in UI):")
    for phase, fraction in phases.items():
        if fraction:
            percentage = float(fraction) * 100.0
            rounded = round(percentage, 1)  # UI shows 1 decimal place
            print(f"{phase}: {rounded:.1f}%")
    
    # Calculate sum of rounded values
    rounded_sum = sum(round(float(fraction) * 100.0, 1) for fraction in phases.values() if fraction)
    print(f"Sum of rounded values: {rounded_sum:.1f}%")

if __name__ == "__main__":
    debug_cement136_display()