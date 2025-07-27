#!/usr/bin/env python3
"""Quick test of D_max=60 behavior"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.services.psd_service import PSDService, PSDParameters, PSDType

# Jeff's exact scenario
print("Jeff's Test: Rosin-Rammler with D_max=60")
print("=" * 45)

service = PSDService()
params = PSDParameters(
    psd_type=PSDType.ROSIN_RAMMLER,
    d50=15.0,    # Default d50
    n=1.4,       # Default n
    dmax=60.0    # Jeff's D_max setting
)

distribution = service.convert_to_discrete(params)

print(f"Generated bins: {len(distribution.points)}")
print(f"Max diameter: {max(distribution.diameters)} μm")
print(f"Expected max: 60 μm")

if max(distribution.diameters) == 60:
    print("✅ CORRECT: Table respects D_max=60")
else:
    print("❌ PROBLEM: Table doesn't respect D_max=60")

print(f"\nLast 5 bins:")
for diameter, mass_fraction in distribution.points[-5:]:
    print(f"  {diameter:3.0f} μm: {mass_fraction*100:5.2f}%")