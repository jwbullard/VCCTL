#!/usr/bin/env python3
"""
Analyze cement151 data which appears to have gypsum fractions.
"""

# cement151 decoded data
hex_data = """0.6324	0.5525
0.1898	0.2585
0.0474	0.0582
0.1256	0.1240
0.0047	0.0068
0.0001	0.0001"""

lines = hex_data.strip().split('\n')
print('cement151 decoded data:')
for i, line in enumerate(lines):
    values = line.split('\t')
    print(f'Row {i}: {values[0]} | {values[1]}')

print('\nLikely interpretation:')
phases = ['C3S', 'C2S', 'C3A', 'C4AF', 'DIHYD', 'HEMIHYD']
for i, (phase, line) in enumerate(zip(phases, lines)):
    values = line.split('\t')
    vol_frac = float(values[0])
    mass_frac = float(values[1])
    print(f'{phase}: volume={vol_frac:.4f}, mass={mass_frac:.4f}')

# Check totals
total_volume = sum(float(line.split('\t')[0]) for line in lines)
total_mass = sum(float(line.split('\t')[1]) for line in lines)
print(f'\nTotals: volume={total_volume:.4f}, mass={total_mass:.4f}')

# Focus on gypsum values
print('\nGypsum fractions for cement151:')
gypsum_lines = lines[4:6]  # Last 2 rows
gypsum_phases = ['DIHYD', 'HEMIHYD']
for phase, line in zip(gypsum_phases, gypsum_lines):
    values = line.split('\t')
    vol_frac = float(values[0])
    mass_frac = float(values[1])
    print(f'{phase}: volume={vol_frac:.4f}, mass={mass_frac:.4f}')