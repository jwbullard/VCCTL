#!/usr/bin/env python3
"""
Normalize cement phase mass fractions to sum to 100% and recalculate volume fractions.

Updates mass fractions for C3S, C2S, C3A, C4AF, K2SO4, Na2SO4 to sum to 1.0 (100%)
Then recalculates volume fractions using the thermodynamic relationship.
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

# Phase specific gravities (g/cm³) - from material dialog
PHASE_SPECIFIC_GRAVITIES = {
    'c3s': 3.15,     # Tricalcium silicate
    'c2s': 3.28,     # Dicalcium silicate
    'c3a': 3.04,     # Tricalcium aluminate
    'c4af': 3.73,    # Tetracalcium aluminoferrite
    'k2so4': 2.66,   # Potassium sulfate
    'na2so4': 2.68   # Sodium sulfate
}

def normalize_mass_fractions(phases_dict):
    """
    Normalize mass fractions to sum to 1.0, preserving relative ratios.
    
    Args:
        phases_dict: Dictionary of phase_key -> mass_fraction values
        
    Returns:
        Dictionary of normalized mass fractions
    """
    # Get non-None values
    valid_phases = {k: v for k, v in phases_dict.items() if v is not None}
    
    if not valid_phases:
        return phases_dict
    
    # Calculate current total
    total = sum(valid_phases.values())
    
    if total == 0:
        return phases_dict
    
    # Calculate normalization factor
    normalization_factor = 1.0 / total
    
    # Apply normalization
    normalized = {}
    for k, v in phases_dict.items():
        if v is not None:
            normalized[k] = v * normalization_factor
        else:
            normalized[k] = None
    
    return normalized

def calculate_volume_fractions(mass_fractions):
    """
    Calculate volume fractions from normalized mass fractions.
    
    Uses the thermodynamic relationship:
    volume_fraction_i = (mass_fraction_i / SG_i) / Σ(mass_fraction_j / SG_j)
    
    Args:
        mass_fractions: Dictionary of phase_key -> mass_fraction values
        
    Returns:
        Dictionary of volume fractions
    """
    # Calculate volume components
    volume_components = {}
    total_volume_component = 0.0
    
    for phase_key, mass_frac in mass_fractions.items():
        if mass_frac is not None and mass_frac > 0:
            sg = PHASE_SPECIFIC_GRAVITIES[phase_key]
            vol_component = mass_frac / sg
            volume_components[phase_key] = vol_component
            total_volume_component += vol_component
        else:
            volume_components[phase_key] = 0.0
    
    # Calculate normalized volume fractions
    volume_fractions = {}
    if total_volume_component > 0:
        for phase_key, vol_component in volume_components.items():
            volume_fractions[phase_key] = vol_component / total_volume_component
    else:
        for phase_key in mass_fractions.keys():
            volume_fractions[phase_key] = 0.0
    
    return volume_fractions

def main():
    """Normalize phase fractions for all cements."""
    
    # Initialize database and service
    db_service = DatabaseService()
    cement_service = CementService(db_service)
    
    # Get all cements
    cements = cement_service.get_all()
    
    updates_made = 0
    errors = 0
    tolerance = 0.005  # 0.5% tolerance for normalization
    
    print("Normalizing cement phase fractions...")
    print(f"Phases: C3S, C2S, C3A, C4AF, K2SO4, Na2SO4")
    print(f"Using tolerance: {tolerance*100:.1f}%")
    print()
    
    for cement in cements:
        # Get current mass fractions
        current_mass = {
            'c3s': cement.c3s_mass_fraction,
            'c2s': cement.c2s_mass_fraction,
            'c3a': cement.c3a_mass_fraction,
            'c4af': cement.c4af_mass_fraction,
            'k2so4': cement.k2so4_mass_fraction,
            'na2so4': cement.na2so4_mass_fraction
        }
        
        # Check if cement has enough phase data
        valid_fractions = [f for f in current_mass.values() if f is not None]
        if len(valid_fractions) < 4:
            continue  # Skip cements without sufficient phase data
        
        # Check if normalization is needed
        current_total = sum(valid_fractions)
        if abs(current_total - 1.0) <= tolerance:
            continue  # Already normalized within tolerance
        
        try:
            print(f"Normalizing {cement.name}:")
            print(f"  Current total: {current_total:.4f} ({current_total*100:.1f}%)")
            
            # Normalize mass fractions
            normalized_mass = normalize_mass_fractions(current_mass)
            
            # Calculate corresponding volume fractions
            normalized_volume = calculate_volume_fractions(normalized_mass)
            
            # Prepare update data
            update_data = CementUpdate(
                # Mass fractions
                c3s_mass_fraction=normalized_mass['c3s'],
                c2s_mass_fraction=normalized_mass['c2s'],
                c3a_mass_fraction=normalized_mass['c3a'],
                c4af_mass_fraction=normalized_mass['c4af'],
                k2so4_mass_fraction=normalized_mass['k2so4'],
                na2so4_mass_fraction=normalized_mass['na2so4'],
                # Volume fractions
                c3s_volume_fraction=normalized_volume['c3s'],
                c2s_volume_fraction=normalized_volume['c2s'],
                c3a_volume_fraction=normalized_volume['c3a'],
                c4af_volume_fraction=normalized_volume['c4af'],
                k2so4_volume_fraction=normalized_volume['k2so4'],
                na2so4_volume_fraction=normalized_volume['na2so4']
            )
            
            # Update cement
            cement_service.update(cement.id, update_data)
            
            # Verify normalization
            new_total_mass = sum([f for f in normalized_mass.values() if f is not None])
            new_total_volume = sum([f for f in normalized_volume.values() if f is not None])
            
            print(f"  New mass total: {new_total_mass:.4f} ({new_total_mass*100:.1f}%)")
            print(f"  New volume total: {new_total_volume:.4f} ({new_total_volume*100:.1f}%)")
            print(f"  ✓ Updated successfully")
            print()
            
            updates_made += 1
            
        except Exception as e:
            print(f"  ✗ Error updating cement '{cement.name}': {e}")
            errors += 1
            print()
    
    print(f"Normalization completed:")
    print(f"  Successfully updated: {updates_made} cements")
    print(f"  Errors encountered: {errors}")
    
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())