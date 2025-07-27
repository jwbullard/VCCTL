#!/usr/bin/env python3
"""
Extract volume and surface fractions from PFC binary data and populate database.
"""

import sqlite3
import sys
from pathlib import Path

def decode_pfc_data(hex_data):
    """Decode hex PFC data and return volume/surface fraction pairs."""
    if not hex_data:
        return []
    
    try:
        # Convert hex to bytes, then to string
        bytes_data = bytes.fromhex(hex_data)
        text_data = bytes_data.decode('utf-8')
        
        # Split into lines and parse pairs
        lines = text_data.strip().split('\n')
        pairs = []
        
        for line in lines:
            if line.strip():
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    volume_fraction = float(parts[0])
                    surface_fraction = float(parts[1])
                    pairs.append((volume_fraction, surface_fraction))
        
        return pairs
    except Exception as e:
        print(f"Error decoding PFC data: {e}")
        return []

def main():
    # Connect to database
    db_path = Path("src/data/database/vcctl.db")
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all cements with PFC data
        cursor.execute("SELECT name, hex(pfc) FROM cement WHERE pfc IS NOT NULL")
        cements = cursor.fetchall()
        
        print(f"Processing {len(cements)} cements with PFC data...")
        
        for name, hex_pfc in cements:
            print(f"\nProcessing {name}...")
            
            # Decode PFC data
            fraction_pairs = decode_pfc_data(hex_pfc)
            
            if not fraction_pairs:
                print(f"  No valid PFC data found")
                continue
            
            print(f"  Found {len(fraction_pairs)} phase rows")
            
            # Initialize all values to 0
            c3s_vol = c3s_surf = 0.0
            c2s_vol = c2s_surf = 0.0  
            c3a_vol = c3a_surf = 0.0
            c4af_vol = c4af_surf = 0.0
            k2so4_vol = k2so4_surf = 0.0
            na2so4_vol = na2so4_surf = 0.0
            
            # Extract values based on number of rows
            if len(fraction_pairs) >= 4:
                # Standard 4 phases
                c3s_vol, c3s_surf = fraction_pairs[0]
                c2s_vol, c2s_surf = fraction_pairs[1]
                c3a_vol, c3a_surf = fraction_pairs[2]
                c4af_vol, c4af_surf = fraction_pairs[3]
                
                print(f"  C3S: vol={c3s_vol:.4f}, surf={c3s_surf:.4f}")
                print(f"  C2S: vol={c2s_vol:.4f}, surf={c2s_surf:.4f}")
                print(f"  C3A: vol={c3a_vol:.4f}, surf={c3a_surf:.4f}")
                print(f"  C4AF: vol={c4af_vol:.4f}, surf={c4af_surf:.4f}")
                
                # Check for K2SO4 and Na2SO4 (rows 5 and 6)
                if len(fraction_pairs) >= 6:
                    k2so4_vol, k2so4_surf = fraction_pairs[4]
                    na2so4_vol, na2so4_surf = fraction_pairs[5]
                    print(f"  K2SO4: vol={k2so4_vol:.4f}, surf={k2so4_surf:.4f}")
                    print(f"  Na2SO4: vol={na2so4_vol:.4f}, surf={na2so4_surf:.4f}")
                else:
                    print(f"  K2SO4: vol=0.0000, surf=0.0000 (default)")
                    print(f"  Na2SO4: vol=0.0000, surf=0.0000 (default)")
            
            # Update database
            update_sql = """
                UPDATE cement SET 
                    c3s_volume_fraction = ?,
                    c3s_surface_fraction = ?,
                    c2s_volume_fraction = ?,
                    c2s_surface_fraction = ?,
                    c3a_volume_fraction = ?,
                    c3a_surface_fraction = ?,
                    c4af_volume_fraction = ?,
                    c4af_surface_fraction = ?,
                    k2so4_volume_fraction = ?,
                    k2so4_surface_fraction = ?,
                    na2so4_volume_fraction = ?,
                    na2so4_surface_fraction = ?
                WHERE name = ?
            """
            
            cursor.execute(update_sql, (
                c3s_vol, c3s_surf,
                c2s_vol, c2s_surf,
                c3a_vol, c3a_surf,
                c4af_vol, c4af_surf,
                k2so4_vol, k2so4_surf,
                na2so4_vol, na2so4_surf,
                name
            ))
            
        # Commit changes
        conn.commit()
        print(f"\n✅ Successfully updated volume and surface fractions for {len(cements)} cements!")
        
        # Verify results
        cursor.execute("""
            SELECT name, 
                   c3s_volume_fraction, c3s_surface_fraction,
                   k2so4_volume_fraction, k2so4_surface_fraction,
                   na2so4_volume_fraction, na2so4_surface_fraction
            FROM cement 
            WHERE k2so4_volume_fraction > 0 OR na2so4_volume_fraction > 0
            ORDER BY name
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"\n📊 Cements with K2SO4 or Na2SO4 data ({len(results)} found):")
            for row in results:
                name, c3s_v, c3s_s, k2so4_v, k2so4_s, na2so4_v, na2so4_s = row
                print(f"  {name}: K2SO4(v={k2so4_v:.4f}, s={k2so4_s:.4f}), Na2SO4(v={na2so4_v:.4f}, s={na2so4_s:.4f})")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()