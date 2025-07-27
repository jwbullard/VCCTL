#!/usr/bin/env python3
"""
Extract gypsum data from Derby CSV hex-encoded fields.
"""

import csv
import sys
from pathlib import Path

def decode_hex_to_string(hex_string):
    """Decode hex string to readable text."""
    try:
        # Remove any whitespace and convert to bytes
        hex_clean = hex_string.strip()
        bytes_data = bytes.fromhex(hex_clean)
        # Try to decode as UTF-8
        return bytes_data.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error decoding hex: {e}")
        return None

def parse_decoded_data(decoded_text):
    """Parse decoded text to extract gypsum values."""
    lines = decoded_text.split('\n')
    gypsum_data = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for patterns that might indicate gypsum data
        # The format might be key-value pairs or structured data
        if 'dihyd' in line.lower() or 'dihydrate' in line.lower():
            # Extract numerical value
            parts = line.split()
            for part in parts:
                try:
                    value = float(part)
                    if 0 <= value <= 1:  # Valid fraction range
                        gypsum_data['dihyd'] = value
                        break
                except ValueError:
                    continue
        elif 'hemihyd' in line.lower() or 'hemihydrate' in line.lower():
            parts = line.split()
            for part in parts:
                try:
                    value = float(part)
                    if 0 <= value <= 1:
                        gypsum_data['hemihyd'] = value
                        break
                except ValueError:
                    continue
        elif 'anhyd' in line.lower() or 'anhydrite' in line.lower():
            parts = line.split()
            for part in parts:
                try:
                    value = float(part)
                    if 0 <= value <= 1:
                        gypsum_data['anhyd'] = value
                        break
                except ValueError:
                    continue
    
    return gypsum_data

def main():
    # Path to Derby CSV file
    csv_path = Path("derby_export/cement.csv")
    
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    print(f"Reading Derby CSV file: {csv_path}")
    
    # Read the CSV file
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        
        row_count = 0
        cement140_found = False
        
        for row in reader:
            row_count += 1
            
            if len(row) < 3:
                continue
                
            cement_name = row[0]
            psd_name = row[1]
            hex_data = row[2]
            
            print(f"\nRow {row_count}: {cement_name}")
            
            # Process all cements to look for gypsum data
            if cement_name in ["cement140", "cement141", "cement136", "cement151", "ustype1"]:
                print(f"Processing {cement_name} in row {row_count}")
                print(f"PSD: {psd_name}")
                print(f"Hex data length: {len(hex_data)} characters")
                
                # Decode the hex data
                decoded_text = decode_hex_to_string(hex_data)
                if decoded_text:
                    print(f"\nDecoded text:")
                    print(decoded_text)
                    
                    # Try to parse numerical data - might be phase fractions
                    lines = decoded_text.strip().split('\n')
                    numerical_data = []
                    for line in lines:
                        if line.strip():
                            parts = line.split('\t')
                            row_data = []
                            for part in parts:
                                try:
                                    value = float(part.strip())
                                    row_data.append(value)
                                except ValueError:
                                    continue
                            if row_data:
                                numerical_data.append(row_data)
                    
                    if numerical_data:
                        print(f"Numerical data matrix:")
                        for i, row_data in enumerate(numerical_data):
                            print(f"  Row {i}: {row_data}")
                        
                        # Check if this could be phase composition data
                        if len(numerical_data) == 4 and all(len(row) == 2 for row in numerical_data):
                            print(f"  Possible phase data (4 phases, 2 values each):")
                            phase_names = ['C3S', 'C2S', 'C3A', 'C4AF']
                            for i, (phase, row_data) in enumerate(zip(phase_names, numerical_data)):
                                print(f"    {phase}: {row_data[0]:.4f}, {row_data[1]:.4f}")
                
                print("-" * 50)
                
                if cement_name == "cement140":
                    cement140_found = True
        
        if not cement140_found:
            print(f"\ncement140 not found in {row_count} rows")
    
    print(f"\nProcessed {row_count} rows total")

if __name__ == "__main__":
    main()