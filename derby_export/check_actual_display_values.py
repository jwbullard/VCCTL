#!/usr/bin/env python3
"""
Check the actual values that would be displayed in the UI for cement136
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

def check_display_values():
    # Get cement136 data
    db_config = DatabaseConfig("vcctl.db")
    db_service = DatabaseService(db_service)
    cement_service = CementService(db_service)

    cement = cement_service.get_by_name('cement136')
    if not cement:
        print("Cement136 not found!")
        return

    print(f"Checking display values for cement: {cement.name}")
    
    # Simulate the exact logic from material_dialog.py _load_material_specific_data
    phase_mapping = {
        'c3s': 'c3s_mass_fraction',
        'c2s': 'c2s_mass_fraction', 
        'c3a': 'c3a_mass_fraction',
        'c4af': 'c4af_mass_fraction',
        'k2so4': 'k2so4_mass_fraction',
        'na2so4': 'na2so4_mass_fraction'
    }
    
    # Convert cement object to dict as would happen in the dialog
    material_data = cement.to_dict()
    
    print("\nPhase values that would be loaded into UI:")
    ui_values = []
    
    for phase_key, db_field in phase_mapping.items():
        value = material_data.get(db_field, 0.0)
        # Convert fraction (0-1) to percentage (0-100) for display
        percentage_value = float(value) * 100.0 if value else 0.0
        
        # Simulate SpinButton rounding (1 decimal place)
        rounded_percentage = round(percentage_value, 1)
        
        ui_values.append(rounded_percentage)
        print(f"{phase_key.upper()}: {value} -> {percentage_value:.15f}% -> UI shows: {rounded_percentage}%")
    
    total_ui = sum(ui_values)
    print(f"\nTotal of UI values: {total_ui}%")
    
    # Also simulate the validation logic
    print(f"\nValidation logic simulation:")
    print(f"sum(spin.get_value() for spin in phase_spins.values()) would be: {total_ui}")

if __name__ == "__main__":
    check_display_values()