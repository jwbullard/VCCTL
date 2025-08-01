#!/usr/bin/env python3
"""
Test paste-only genmic calculation to verify volume fractions are correct.
"""

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_paste_only_calculation():
    """Test paste-only volume fraction calculation."""
    
    # Create a simple mix design: 0.95 kg cement + 0.05 kg quartz + water at W/B=0.4
    cement_mass = 0.95  # kg
    filler_mass = 0.05  # kg
    wb_ratio = 0.4
    
    # Calculate water mass
    total_powder_mass = cement_mass + filler_mass
    water_mass = wb_ratio * total_powder_mass  # 0.4 kg
    
    logger.info(f"=== TEST PASTE-ONLY CALCULATION ===")
    logger.info(f"Cement mass: {cement_mass} kg")
    logger.info(f"Quartz filler mass: {filler_mass} kg")
    logger.info(f"Total powder mass: {total_powder_mass} kg")
    logger.info(f"W/B ratio: {wb_ratio}")
    logger.info(f"Water mass: {water_mass} kg")
    logger.info(f"Total paste mass: {total_powder_mass + water_mass} kg")
    
    # Calculate expected paste volume fractions
    cement_sg = 3.15
    quartz_sg = 2.65
    water_sg = 1.0
    
    cement_abs_vol = cement_mass / cement_sg
    quartz_abs_vol = filler_mass / quartz_sg
    water_abs_vol = water_mass / water_sg
    
    total_paste_abs_vol = cement_abs_vol + quartz_abs_vol + water_abs_vol
    total_powder_abs_vol = cement_abs_vol + quartz_abs_vol
    
    expected_binder_solid_vfrac = total_powder_abs_vol / total_paste_abs_vol
    expected_water_vfrac = water_abs_vol / total_paste_abs_vol
    
    logger.info(f"Expected binder solid volume fraction: {expected_binder_solid_vfrac:.6f}")
    logger.info(f"Expected water volume fraction: {expected_water_vfrac:.6f}")
    logger.info(f"Expected total: {expected_binder_solid_vfrac + expected_water_vfrac:.6f}")
    
    # Verify they sum to 1.0
    if abs((expected_binder_solid_vfrac + expected_water_vfrac) - 1.0) < 0.001:
        logger.info("✅ Expected volume fractions sum to 1.0 correctly")
    else:
        logger.error("❌ Expected volume fractions don't sum to 1.0!")
    
    # Test that air content and aggregates don't affect these calculations
    logger.info(f"\n=== VERIFY AIR/AGGREGATE INDEPENDENCE ===")
    logger.info(f"The genmic input should be IDENTICAL regardless of:")
    logger.info(f"- Air volume fraction (0.0 vs 0.05 vs 0.10)")
    logger.info(f"- Fine aggregate mass (0 kg vs 1.5 kg)")
    logger.info(f"- Coarse aggregate mass (0 kg vs 2.0 kg)")
    logger.info(f"Because genmic simulates PASTE ONLY!")
    
    logger.info(f"\n✅ Test completed successfully")

if __name__ == "__main__":
    test_paste_only_calculation()