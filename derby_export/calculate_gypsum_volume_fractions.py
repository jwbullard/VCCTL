#!/usr/bin/env python3
"""
Calculate and update gypsum volume fractions from mass fractions.

Uses the thermodynamic relationship:
volume_fraction_i = (mass_fraction_i / SG_i) / Σ(mass_fraction_j / SG_j)

Specific gravity values:
- Dihydrate (CaSO4·2H2O): 2.32
- Hemihydrate (CaSO4·0.5H2O): 2.74  
- Anhydrite (CaSO4): 2.61
"""

import sys
from pathlib import Path

# Add the src directory to Python path to import VCCTL modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from app.database.service import DatabaseService
from app.services.cement_service import CementService
from app.models.cement import CementUpdate

# Specific gravity constants
SG_DIHYDRATE = 2.32    # CaSO4·2H2O
SG_HEMIHYDRATE = 2.74  # CaSO4·0.5H2O  
SG_ANHYDRITE = 2.61    # CaSO4

def calculate_gypsum_volume_fractions(mass_dihyd, mass_hemihyd, mass_anhyd, cement_bulk_sg=3.15):
    """
    Calculate volume fractions from mass fractions using specific gravities.
    
    Mass fractions are in units of g component / 100 g total cement.
    Volume fractions are in units of cm³ component / 100 cm³ total cement.
    
    Formula: volume_fraction_i = (mass_fraction_i / SG_i) × cement_bulk_SG
    
    Args:
        mass_dihyd: Dihydrate mass fraction (0-1)
        mass_hemihyd: Hemihydrate mass fraction (0-1)
        mass_anhyd: Anhydrite mass fraction (0-1)
        cement_bulk_sg: Bulk specific gravity of cement (default 3.15)
        
    Returns:
        tuple: (vol_dihyd, vol_hemihyd, vol_anhyd)
    """
    # Handle None values
    mass_dihyd = mass_dihyd or 0.0
    mass_hemihyd = mass_hemihyd or 0.0
    mass_anhyd = mass_anhyd or 0.0
    
    # Calculate volume fractions using correct formula
    # volume_fraction = (mass_fraction / component_SG) * cement_bulk_SG
    vol_fraction_dihyd = (mass_dihyd / SG_DIHYDRATE) * cement_bulk_sg
    vol_fraction_hemihyd = (mass_hemihyd / SG_HEMIHYDRATE) * cement_bulk_sg
    vol_fraction_anhyd = (mass_anhyd / SG_ANHYDRITE) * cement_bulk_sg
    
    return vol_fraction_dihyd, vol_fraction_hemihyd, vol_fraction_anhyd

def main():
    """Calculate and update gypsum volume fractions for all cements."""
    
    # Initialize database and service
    db_service = DatabaseService()
    cement_service = CementService(db_service)
    
    # Get all cements
    cements = cement_service.get_all()
    
    updates_made = 0
    errors = 0
    
    print("Calculating gypsum volume fractions from mass fractions...")
    print(f"Using specific gravities: DIHYD={SG_DIHYDRATE}, HEMIHYD={SG_HEMIHYDRATE}, ANHYD={SG_ANHYDRITE}")
    print("Using cement bulk specific gravity: 3.15")
    print("Formula: volume_fraction = (mass_fraction / component_SG) × cement_bulk_SG")
    print()
    
    for cement in cements:
        # Skip if no gypsum mass fraction data
        if not cement.has_gypsum_data:
            continue
            
        try:
            # Calculate volume fractions
            vol_dihyd, vol_hemihyd, vol_anhyd = calculate_gypsum_volume_fractions(
                cement.dihyd, cement.hemihyd, cement.anhyd
            )
            
            # Update cement with volume fractions
            update_data = CementUpdate(
                dihyd_volume_fraction=vol_dihyd,
                hemihyd_volume_fraction=vol_hemihyd,
                anhyd_volume_fraction=vol_anhyd
            )
            
            cement_service.update(cement.id, update_data)
            
            # Display results
            mass_total = (cement.dihyd or 0) + (cement.hemihyd or 0) + (cement.anhyd or 0)
            vol_total = vol_dihyd + vol_hemihyd + vol_anhyd
            
            print(f"{cement.name}:")
            print(f"  Mass fractions: DIHYD={cement.dihyd:.4f}, HEMIHYD={cement.hemihyd:.4f}, ANHYD={cement.anhyd:.4f} (sum={mass_total:.4f})")
            print(f"  Vol fractions:  DIHYD={vol_dihyd:.4f}, HEMIHYD={vol_hemihyd:.4f}, ANHYD={vol_anhyd:.4f} (sum={vol_total:.4f})")
            print()
            
            updates_made += 1
            
        except Exception as e:
            print(f"Error updating cement '{cement.name}': {e}")
            errors += 1
    
    print(f"Volume fraction calculation completed:")
    print(f"  Successfully updated: {updates_made} cements")
    print(f"  Errors encountered: {errors}")
    
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())