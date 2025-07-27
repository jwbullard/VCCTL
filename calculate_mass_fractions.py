#!/usr/bin/env python3
"""
Calculate mass fractions from volume fractions using phase-specific gravities.
"""

import sqlite3
import sys
from pathlib import Path

# Phase specific gravities (g/cm³)
PHASE_SPECIFIC_GRAVITIES = {
    'c3s': 3.15,     # From microstructure_service.py
    'c2s': 3.28,     # From microstructure_service.py
    'c3a': 3.04,     # From microstructure_service.py
    'c4af': 3.73,    # From microstructure_service.py
    'k2so4': 2.66,   # Literature value for potassium sulfate
    'na2so4': 2.68   # Literature value for sodium sulfate
}

def calculate_mass_fractions_from_volume(volume_fractions, specific_gravities):
    """
    Calculate mass fractions from volume fractions using specific gravities.
    
    Formula: mass_fraction_i = (volume_fraction_i × SG_i) / Σ(volume_fraction_j × SG_j)
    
    Args:
        volume_fractions: dict of phase -> volume fraction
        specific_gravities: dict of phase -> specific gravity
    
    Returns:
        dict of phase -> mass fraction
    """
    # Calculate weighted volumes (volume × specific gravity)
    weighted_volumes = {}
    total_weighted_volume = 0.0
    
    for phase, vol_frac in volume_fractions.items():
        if vol_frac > 0:  # Only consider phases with non-zero volume
            sg = specific_gravities.get(phase, 1.0)
            weighted_vol = vol_frac * sg
            weighted_volumes[phase] = weighted_vol
            total_weighted_volume += weighted_vol
    
    # Calculate mass fractions
    mass_fractions = {}
    for phase, weighted_vol in weighted_volumes.items():
        if total_weighted_volume > 0:
            mass_fractions[phase] = weighted_vol / total_weighted_volume
        else:
            mass_fractions[phase] = 0.0
    
    # Ensure all phases are included (even zero ones)
    for phase in volume_fractions.keys():
        if phase not in mass_fractions:
            mass_fractions[phase] = 0.0
    
    return mass_fractions

def main():
    # Connect to database
    db_path = Path("src/data/database/vcctl.db")
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all cements with volume fraction data
        cursor.execute("""
            SELECT name, 
                   c3s_volume_fraction, c2s_volume_fraction, c3a_volume_fraction, 
                   c4af_volume_fraction, k2so4_volume_fraction, na2so4_volume_fraction,
                   c3s_mass_fraction, c2s_mass_fraction, c3a_mass_fraction, 
                   c4af_mass_fraction, k2so4_mass_fraction, na2so4_mass_fraction
            FROM cement 
            WHERE c3s_volume_fraction IS NOT NULL
            ORDER BY name
        """)
        
        cements = cursor.fetchall()
        print(f"Processing {len(cements)} cements...")
        
        for row in cements:
            name = row[0]
            
            # Volume fractions
            vol_fractions = {
                'c3s': row[1] or 0.0,
                'c2s': row[2] or 0.0,
                'c3a': row[3] or 0.0,
                'c4af': row[4] or 0.0,
                'k2so4': row[5] or 0.0,
                'na2so4': row[6] or 0.0
            }
            
            # Current mass fractions (for comparison)
            current_mass = {
                'c3s': row[7] or 0.0,
                'c2s': row[8] or 0.0,
                'c3a': row[9] or 0.0,
                'c4af': row[10] or 0.0,
                'k2so4': row[11] or 0.0,
                'na2so4': row[12] or 0.0
            }
            
            # Calculate new mass fractions from volume fractions
            calculated_mass = calculate_mass_fractions_from_volume(vol_fractions, PHASE_SPECIFIC_GRAVITIES)
            
            print(f"\n{name}:")
            print(f"  Volume fractions: C3S={vol_fractions['c3s']:.4f}, C2S={vol_fractions['c2s']:.4f}, C3A={vol_fractions['c3a']:.4f}, C4AF={vol_fractions['c4af']:.4f}")
            if vol_fractions['k2so4'] > 0 or vol_fractions['na2so4'] > 0:
                print(f"                    K2SO4={vol_fractions['k2so4']:.4f}, Na2SO4={vol_fractions['na2so4']:.4f}")
            
            print(f"  Current mass:     C3S={current_mass['c3s']:.4f}, C2S={current_mass['c2s']:.4f}, C3A={current_mass['c3a']:.4f}, C4AF={current_mass['c4af']:.4f}")
            if current_mass['k2so4'] > 0 or current_mass['na2so4'] > 0:
                print(f"                    K2SO4={current_mass['k2so4']:.4f}, Na2SO4={current_mass['na2so4']:.4f}")
            
            print(f"  Calculated mass:  C3S={calculated_mass['c3s']:.4f}, C2S={calculated_mass['c2s']:.4f}, C3A={calculated_mass['c3a']:.4f}, C4AF={calculated_mass['c4af']:.4f}")
            if calculated_mass['k2so4'] > 0 or calculated_mass['na2so4'] > 0:
                print(f"                    K2SO4={calculated_mass['k2so4']:.4f}, Na2SO4={calculated_mass['na2so4']:.4f}")
            
            # Calculate total for verification
            total_calc = sum(calculated_mass.values())
            total_current = sum(v for v in current_mass.values() if v > 0)
            print(f"  Totals: Current={total_current:.4f}, Calculated={total_calc:.4f}")
            
            # Update database with calculated mass fractions
            update_sql = """
                UPDATE cement SET 
                    c3s_mass_fraction = ?,
                    c2s_mass_fraction = ?,
                    c3a_mass_fraction = ?,
                    c4af_mass_fraction = ?,
                    k2so4_mass_fraction = ?,
                    na2so4_mass_fraction = ?
                WHERE name = ?
            """
            
            cursor.execute(update_sql, (
                calculated_mass['c3s'],
                calculated_mass['c2s'],
                calculated_mass['c3a'],
                calculated_mass['c4af'],
                calculated_mass['k2so4'],
                calculated_mass['na2so4'],
                name
            ))
        
        # Commit changes
        conn.commit()
        print(f"\n✅ Successfully updated mass fractions for {len(cements)} cements!")
        
        # Show summary of cements with K2SO4/Na2SO4
        cursor.execute("""
            SELECT name, k2so4_mass_fraction, na2so4_mass_fraction
            FROM cement 
            WHERE k2so4_mass_fraction > 0 OR na2so4_mass_fraction > 0
            ORDER BY name
        """)
        
        k_na_cements = cursor.fetchall()
        if k_na_cements:
            print(f"\n📊 Cements with K2SO4 or Na2SO4 mass fractions ({len(k_na_cements)} found):")
            for name, k2so4_mass, na2so4_mass in k_na_cements:
                print(f"  {name}: K2SO4={k2so4_mass:.4f} ({k2so4_mass*100:.2f}%), Na2SO4={na2so4_mass:.4f} ({na2so4_mass*100:.2f}%)")
        
        # Verify totals
        cursor.execute("""
            SELECT name,
                   (c3s_mass_fraction + c2s_mass_fraction + c3a_mass_fraction + 
                    c4af_mass_fraction + COALESCE(k2so4_mass_fraction,0) + COALESCE(na2so4_mass_fraction,0)) as total
            FROM cement 
            WHERE c3s_mass_fraction IS NOT NULL
            ORDER BY ABS(total - 1.0) DESC
            LIMIT 5
        """)
        
        print(f"\n🔍 Mass fraction totals (top 5 largest deviations from 1.0):")
        for name, total in cursor.fetchall():
            deviation = abs(total - 1.0)
            print(f"  {name}: {total:.4f} (deviation: {deviation:.4f})")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()