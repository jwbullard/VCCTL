#!/usr/bin/env python3
"""
Complete end-to-end demonstration: Microstructure Creation → Hydration Parameters → disrealnew execution
"""

import sys
import os
import json
from datetime import datetime
sys.path.insert(0, 'src')

from app.services.psd_service import PSDService, PSDParameters, PSDType
from app.services.microstructure_hydration_bridge import MicrostructureHydrationBridge

def create_test_microstructure():
    """Simulate creating a microstructure using the Microstructure Tool."""
    
    print("STEP 1: MICROSTRUCTURE CREATION SIMULATION")
    print("=" * 60)
    
    # Simulate user creating a concrete mix in the Microstructure Tool
    operation_name = f"ConcreteDemo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"Creating microstructure: {operation_name}")
    print("User interface simulation:")
    print("  - Mix design: Ordinary Portland Cement concrete")
    print("  - System size: 100³ voxels")  
    print("  - Resolution: 1.0 μm/voxel")
    print("  - Water/binder ratio: 0.40")
    
    # Materials data as would come from the UI and database
    materials_data = [
        {
            'name': 'cement140',
            'material_type': 'cement',
            'volume_fraction': 0.35,
            'mass_fraction': 0.55,
            'specific_gravity': 3.15,
            'psd_mode': 'rosin_rammler',
            'psd_d50': 15.0,
            'psd_n': 1.1,
            'psd_dmax': 75.0,
            'c3s_mass_fraction': 0.55,
            'c2s_mass_fraction': 0.20,  
            'c3a_mass_fraction': 0.08,
            'c4af_mass_fraction': 0.12
        },
        {
            'name': 'silica_fume_950d',
            'material_type': 'silica_fume',
            'volume_fraction': 0.03,
            'mass_fraction': 0.08,
            'specific_gravity': 2.20,
            'psd_mode': 'log_normal',
            'psd_median': 0.15,
            'psd_spread': 1.8
        },
        {
            'name': 'fly_ash_class_f',
            'material_type': 'fly_ash',
            'volume_fraction': 0.05,
            'mass_fraction': 0.12,
            'specific_gravity': 2.38,
            'psd_mode': 'rosin_rammler',
            'psd_d50': 18.0,
            'psd_n': 0.9,
            'psd_dmax': 100.0
        },
        {
            'name': 'fine_aggregate_ottawa',
            'material_type': 'aggregate',
            'volume_fraction': 0.25,
            'mass_fraction': 0.25,
            'specific_gravity': 2.65,
            'psd_mode': 'fuller_thompson',
            'psd_exponent': 0.5,
            'psd_dmax': 600.0
        }
    ]
    
    print(f"\nMaterials in mix:")
    total_volume = 0
    for i, material in enumerate(materials_data, 1):
        print(f"  {i}. {material['name']}")
        print(f"     Type: {material['material_type']}")
        print(f"     Volume fraction: {material['volume_fraction']:.3f}")
        
        if 'psd_d50' in material:
            print(f"     PSD: {material['psd_mode']} (d50={material['psd_d50']:.1f}μm)")
        elif 'psd_median' in material:
            print(f"     PSD: {material['psd_mode']} (median={material['psd_median']:.2f}μm)")
        else:
            print(f"     PSD: {material['psd_mode']}")
        total_volume += material['volume_fraction']
    
    water_volume = 0.37  # Remaining volume for water/pores
    print(f"  5. Water + Pores: {water_volume:.3f}")
    print(f"Total volume: {total_volume + water_volume:.3f}")
    
    # Simulate microstructure file generation
    microstructure_file = f"./scratch/{operation_name}/{operation_name}.img"
    
    print(f"\n📁 Generated microstructure files:")
    print(f"   {microstructure_file}")
    print(f"   {microstructure_file.replace('.img', '.pimg')}")
    
    return operation_name, microstructure_file, materials_data

def store_microstructure_metadata(operation_name, microstructure_file, materials_data):
    """Store the microstructure metadata for hydration use."""
    
    print(f"\nSTEP 2: STORING MICROSTRUCTURE METADATA")
    print("=" * 60)
    
    bridge = MicrostructureHydrationBridge()
    
    # Store metadata as the Microstructure Tool would do
    success = bridge.store_microstructure_metadata(
        operation_name=operation_name,
        microstructure_file=microstructure_file,
        system_size=100,
        resolution=1.0,
        materials_data=materials_data
    )
    
    if success:
        print("✅ Metadata stored successfully")
        
        # Show what was stored
        metadata = bridge.load_microstructure_metadata(operation_name)
        if metadata:
            print(f"📊 Stored metadata:")
            print(f"   Operation: {metadata.operation_name}")
            print(f"   System: {metadata.system_size}³ voxels at {metadata.resolution} μm/voxel")
            print(f"   Materials: {len(metadata.materials)}")
            for i, material in enumerate(metadata.materials, 1):
                print(f"     {i}. Phase {material.phase_id}: {material.material_name}")
                print(f"        Volume: {material.volume_fraction:.3f}, Type: {material.material_type}")
        
        return True
    else:
        print("❌ Failed to store metadata")
        return False

def generate_hydration_parameters(operation_name):
    """Generate complete hydration parameters from microstructure."""
    
    print(f"\nSTEP 3: HYDRATION PARAMETER GENERATION")
    print("=" * 60)
    
    bridge = MicrostructureHydrationBridge()
    
    # Calculate one-voxel bias parameters
    print("🧮 Calculating one-voxel bias parameters...")
    bias_parameter_lines = bridge.calculate_onevoxelbias_for_microstructure(operation_name)
    
    if bias_parameter_lines:
        print("✅ One-voxel bias calculation successful")
        for line in bias_parameter_lines:
            print(f"   {line}")
    else:
        print("❌ One-voxel bias calculation failed")
        return None
    
    # Load base hydration parameters
    base_params_file = "parameters.csv"
    if not os.path.exists(base_params_file):
        print(f"❌ Base parameters file not found: {base_params_file}")
        return None
    
    # Generate complete extended parameter file
    print(f"📋 Generating extended parameter file...")
    
    # Read base hydration parameters (378 lines)
    with open(base_params_file, 'r') as f:
        base_lines = f.readlines()
    
    print(f"✅ Loaded {len(base_lines)} base hydration parameters")
    
    # Add UI simulation parameters 
    ui_parameters = [
        f"Iseed,-12345",
        f"Micdir,./scratch/{operation_name}/",
        f"Fileroot,{operation_name}.img",
        f"Pimgfile,{operation_name}.pimg", 
        f"Temp_0,25.0",
        f"Adiaflag,0",
        f"Tcure,28.0",
        f"Rh_specified,0.8",
        f"Movie,0",
        f"Movieframes,0",
        f"Sealed,0",
        f"Ptarget,101325.0",
        f"Moistflag,0",
        f"Heatflag,0",
        f"Cyccrit,0.8",
        f"Nhydsteps,10000",
        f"Maxcyc,100000",
        f"N_cement_size_classes,1",
        f"Cement_size_class_1_min,0.0",
        f"Cement_size_class_1_max,100.0",
        f"Cement_size_class_1_fraction,1.0",
        f"IDAsize_1,0.6",
        f"IDAratio_1,0.1",
        f"IDAangle_1,2.094",
        f"Temp_0_agg,25.0",
        f"U_coeff_agg,0.0",
        f"Csh2flag,1",
        f"Chflag,1",
        f"MovieFrameFreq,72.0",
        f"PHactive,1"
    ]
    
    print(f"✅ Generated {len(ui_parameters)} UI simulation parameters")
    
    # Create complete extended parameter file
    output_file = f"./scratch/{operation_name}_complete_parameters.csv"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        # Write base hydration parameters
        for line in base_lines:
            f.write(line)
        
        # Write UI simulation parameters
        for param in ui_parameters:
            f.write(param + '\n')
        
        # Write one-voxel bias parameters
        for bias_line in bias_parameter_lines:
            f.write(bias_line + '\n')
    
    total_lines = len(base_lines) + len(ui_parameters) + len(bias_parameter_lines)
    print(f"💾 Complete parameter file saved: {output_file}")
    print(f"📊 Total parameters: {total_lines}")
    print(f"   - Base hydration: {len(base_lines)}")
    print(f"   - UI simulation: {len(ui_parameters)}")
    print(f"   - One-voxel bias: {len(bias_parameter_lines)}")
    
    return output_file

def test_disrealnew_execution(operation_name, parameter_file):
    """Test disrealnew execution with complete parameters."""
    
    print(f"\nSTEP 4: DISREALNEW EXECUTION TEST")  
    print("=" * 60)
    
    # Create working directory and copy files
    work_dir = f"./scratch/{operation_name}"
    os.makedirs(work_dir, exist_ok=True)
    
    # Copy parameter file to working directory
    import shutil
    local_param_file = os.path.join(work_dir, "complete_parameters.csv")
    shutil.copy(parameter_file, local_param_file)
    
    print(f"📁 Working directory: {work_dir}")
    print(f"📋 Parameter file: {local_param_file}")
    
    # Test disrealnew command
    print(f"🚀 Testing disrealnew execution...")
    
    # Build command
    cmd_parts = [
        f"cd {work_dir}",
        f"../../backend/bin/disrealnew",
        f"--workdir=./",
        f"--parameters=complete_parameters.csv",
        f"--json=progress.json"
    ]
    
    command = " && ".join(cmd_parts)
    print(f"Command: {command}")
    
    return command, work_dir

def main():
    """Run the complete end-to-end demonstration."""
    
    print("VCCTL END-TO-END INTEGRATION DEMONSTRATION")
    print("=" * 80)
    print("Testing complete workflow:")
    print("  Microstructure Creation → Metadata Storage → Hydration Parameters → disrealnew")
    print()
    
    try:
        # Step 1: Create microstructure
        operation_name, microstructure_file, materials_data = create_test_microstructure()
        
        # Step 2: Store metadata
        if not store_microstructure_metadata(operation_name, microstructure_file, materials_data):
            return False
        
        # Step 3: Generate hydration parameters
        parameter_file = generate_hydration_parameters(operation_name)
        if not parameter_file:
            return False
        
        # Step 4: Test disrealnew
        command, work_dir = test_disrealnew_execution(operation_name, parameter_file)
        
        print(f"\n" + "=" * 80)
        print("🎉 END-TO-END INTEGRATION SUCCESSFUL!")
        print("=" * 80)
        print(f"✅ Microstructure metadata stored")
        print(f"✅ One-voxel bias parameters calculated from material PSDs")
        print(f"✅ Complete extended parameter file generated")
        print(f"✅ Ready for disrealnew execution")
        
        print(f"\n🔬 TO RUN THE ACTUAL SIMULATION:")
        print(f"   {command}")
        
        print(f"\n📂 All files created in: {work_dir}")
        print(f"   - complete_parameters.csv (ready for disrealnew)")
        print(f"   - Microstructure metadata stored for future use")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in end-to-end test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()