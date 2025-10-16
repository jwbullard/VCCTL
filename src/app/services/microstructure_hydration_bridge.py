#!/usr/bin/env python3
"""
Microstructure-Hydration Bridge Service

Handles data exchange between Microstructure Tool and Hydration Tool,
specifically for one-voxel bias parameter generation.
"""

import os
import json
import logging
import shutil
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from app.services.one_voxel_bias_service import OneVoxelBiasService, OneVoxelBiasResult
from app.services.psd_service import PSDService, PSDParameters, DiscreteDistribution, PSDType


@dataclass
class MicrostructureMaterialInfo:
    """Information about a material used in microstructure generation."""
    phase_id: int
    material_name: str
    material_type: str  # 'cement', 'fly_ash', 'slag', etc.
    volume_fraction: float
    mass_fraction: float
    specific_gravity: float
    psd_parameters: Dict[str, Any]  # Original PSD parameters from database
    
    
@dataclass 
class MicrostructureMetadata:
    """Complete metadata for a microstructure generation."""
    operation_name: str
    microstructure_file: str  # Path to .img file
    system_size: int
    resolution: float  # μm per voxel
    materials: List[MicrostructureMaterialInfo]
    generation_timestamp: str
    

class MicrostructureHydrationBridge:
    """
    Service for data exchange between Microstructure and Hydration tools.
    
    Responsibilities:
    1. Store microstructure material metadata during generation
    2. Retrieve metadata for hydration parameter calculation  
    3. Calculate one-voxel bias from original PSD data
    4. Generate extended parameter file entries
    """
    
    def __init__(self, db_service=None):
        self.logger = logging.getLogger(__name__)
        self.db_service = db_service
        self.psd_service = PSDService()
        self.bias_service = OneVoxelBiasService()

        # Get operations directory from configuration
        from app.services.service_container import get_service_container
        service_container = get_service_container()
        self.operations_dir = service_container.directories_service.get_operations_path()

        # Metadata storage directory (in operations directory)
        self.metadata_dir = os.path.join(str(self.operations_dir), "microstructure_metadata")
        os.makedirs(self.metadata_dir, exist_ok=True)
    
    def store_microstructure_metadata(self, operation_name: str, 
                                    microstructure_file: str,
                                    system_size: int,
                                    resolution: float,
                                    materials_data: List[Dict[str, Any]]) -> bool:
        """
        Store microstructure metadata for later hydration use.
        
        Args:
            operation_name: Name of microstructure operation
            microstructure_file: Path to generated .img file
            system_size: System size in voxels
            resolution: Resolution in μm per voxel
            materials_data: List of material data from UI/database
            
        Returns:
            Success status
        """
        try:
            # Convert materials data to structured format
            materials = []
            phase_id = 1  # Start from 1 (0 is typically pore)
            
            for material_data in materials_data:
                material_info = MicrostructureMaterialInfo(
                    phase_id=phase_id,
                    material_name=material_data.get('name', f'Material_{phase_id}'),
                    material_type=material_data.get('material_type', 'unknown'),
                    volume_fraction=material_data.get('volume_fraction', 0.0),
                    mass_fraction=material_data.get('mass_fraction', 0.0), 
                    specific_gravity=material_data.get('specific_gravity', 2.65),
                    psd_parameters=self._extract_psd_parameters(material_data)
                )
                materials.append(material_info)
                phase_id += 1
            
            # Create metadata structure
            metadata = MicrostructureMetadata(
                operation_name=operation_name,
                microstructure_file=microstructure_file,
                system_size=system_size,
                resolution=resolution,
                materials=materials,
                generation_timestamp=datetime.utcnow().isoformat()
            )
            
            # Save to JSON file
            metadata_file = os.path.join(self.metadata_dir, f"{operation_name}_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)
            
            self.logger.info(f"Stored microstructure metadata: {metadata_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store microstructure metadata: {e}")
            return False
    
    def load_microstructure_metadata(self, operation_name: str) -> Optional[MicrostructureMetadata]:
        """Load microstructure metadata from storage."""
        try:
            metadata_file = os.path.join(self.metadata_dir, f"{operation_name}_metadata.json")
            
            if not os.path.exists(metadata_file):
                self.logger.warning(f"Metadata file not found: {metadata_file}")
                return None
            
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to dataclass
            materials = []
            for material_data in data['materials']:
                material = MicrostructureMaterialInfo(**material_data)
                materials.append(material)
            
            metadata = MicrostructureMetadata(
                operation_name=data['operation_name'],
                microstructure_file=data['microstructure_file'],
                system_size=data['system_size'],
                resolution=data['resolution'],
                materials=materials,
                generation_timestamp=data['generation_timestamp']
            )
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to load microstructure metadata: {e}")
            return None
    
    def calculate_onevoxelbias_for_microstructure(self, operation_name: str) -> List[str]:
        """
        Calculate one-voxel bias parameters for a microstructure.
        
        Args:
            operation_name: Name of microstructure operation
            
        Returns:
            List of parameter lines for extended parameter file
        """
        try:
            # Load metadata
            metadata = self.load_microstructure_metadata(operation_name)
            if not metadata:
                raise ValueError(f"No metadata found for microstructure: {operation_name}")
            
            # Calculate bias for each material
            bias_results = []
            
            for material in metadata.materials:
                # Convert PSD parameters to discrete distribution
                psd_params = self._dict_to_psd_parameters(material.psd_parameters)
                discrete_psd = self.psd_service.convert_to_discrete(psd_params)
                
                # Calculate quantized diameters (use smallest discrete diameters)
                sorted_diameters = sorted(set(discrete_psd.diameters))
                quantized_diameters = sorted_diameters[:10]  # Use first 10
                
                # Calculate bias using the discrete PSD
                bias_result = self._calculate_material_bias(
                    material, discrete_psd, quantized_diameters
                )
                bias_results.append(bias_result)
            
            # Generate parameter lines
            parameter_lines = self.bias_service.generate_onevoxelbias_parameters(bias_results)
            
            self.logger.info(f"Calculated one-voxel bias for {len(bias_results)} materials")
            return parameter_lines
            
        except Exception as e:
            self.logger.error(f"Failed to calculate one-voxel bias: {e}")
            self.logger.warning("Using default one-voxel bias values")
            # Return default bias values when metadata is missing
            return [
                "Onevoxelbias,1,1.0",  # Default cement bias
                "Onevoxelbias,2,1.0",  # Default fly ash bias  
                "Onevoxelbias,3,1.0",  # Default slag bias
                "Onevoxelbias,4,1.0"   # Default silica fume bias
            ]
    
    def generate_extended_parameter_file(self, operation_name: str, microstructure_name: str, 
                                       curing_conditions: Dict[str, Any],
                                       time_calibration_settings: Dict[str, Any] = None,
                                       advanced_settings: Dict[str, Any] = None,
                                       db_parameter_modifications: Dict[str, Any] = None,
                                       max_time_hours: float = 168.0) -> str:
        """
        Generate complete extended parameter file for disrealnew.c.
        
        Args:
            operation_name: Name for the hydration operation
            microstructure_name: Name of the microstructure operation to use
            curing_conditions: Dict with thermal and moisture conditions
            time_calibration_settings: Dict with time calibration mode and parameters
            advanced_settings: Dict with advanced simulation parameters
            db_parameter_modifications: Dict with user modifications to database parameters
            max_time_hours: Maximum simulation time in hours for End_time parameter
            
        Returns:
            Path to generated parameter file
        """
        try:
            from app.services.hydration_parameters_service import HydrationParametersService
            from app.services.service_container import get_service_container
            
            # Get services
            service_container = get_service_container()
            hydration_service = HydrationParametersService(service_container.database_service)
            
            # Load base hydration parameters 
            base_params = hydration_service.get_parameter_set("portland_cement_standard")
            if not base_params:
                raise ValueError("Base hydration parameters not found")
            
            # Apply database parameter modifications if provided
            if db_parameter_modifications:
                # Create a copy of parameters and apply modifications
                modified_parameters = base_params.parameters.copy()
                modified_parameters.update(db_parameter_modifications)
                
                # Update the base_params object
                base_params.parameters = modified_parameters
                
                self.logger.info(f"Applied {len(db_parameter_modifications)} parameter modifications")
            
            # Get one-voxel bias parameters for the microstructure
            bias_parameters = self.calculate_onevoxelbias_for_microstructure(microstructure_name)
            
            # Generate UI simulation parameters with curing conditions, time calibration, and advanced settings
            ui_parameters = self._generate_ui_simulation_parameters(
                microstructure_name, curing_conditions, time_calibration_settings, advanced_settings, max_time_hours, operation_name
            )
            
            # Create operation directory
            operation_dir = str(self.operations_dir / operation_name)
            os.makedirs(operation_dir, exist_ok=True)
            
            # Copy microstructure files to operation directory
            self._copy_microstructure_files(microstructure_name, operation_dir)

            # Generate extended parameter file
            param_file_path = str(self.operations_dir / operation_name / f"{operation_name}_extended_parameters.csv")
            
            with open(param_file_path, 'w') as f:
                # Write base hydration parameters (378 parameters)
                base_param_lines = base_params.export_to_csv_lines()
                for line in base_param_lines:
                    f.write(line + '\n')
                
                # Write UI simulation parameters with one-voxel bias inserted at correct location
                for param in ui_parameters:
                    f.write(param + '\n')
                    # Insert one-voxel bias parameters after Outtimefreq
                    if param.startswith("Outtimefreq,"):
                        for bias_line in bias_parameters:
                            f.write(bias_line + '\n')
            
            total_lines = len(base_param_lines) + len(ui_parameters) + len(bias_parameters)
            self.logger.info(f"Generated extended parameter file with {total_lines} parameters: {param_file_path}")
            
            # Generate required alkali data files
            self._generate_alkali_files(microstructure_name, operation_dir)
            
            # Generate required slag characteristics file
            self._generate_slag_file(operation_dir)
            
            return param_file_path
            
        except Exception as e:
            self.logger.error(f"Failed to generate extended parameter file: {e}")
            raise
    
    def _generate_ui_simulation_parameters(self, microstructure_name: str, 
                                         curing_conditions: Dict[str, Any],
                                         time_calibration_settings: Dict[str, Any] = None,
                                         advanced_settings: Dict[str, Any] = None,
                                         max_time_hours: float = 168.0,
                                         operation_name: str = None) -> List[str]:
        """
        Generate UI simulation parameters including curing conditions, time calibration, and advanced settings.
        
        Args:
            microstructure_name: Name of microstructure operation
            curing_conditions: Dict with thermal and moisture settings
            time_calibration_settings: Dict with time calibration mode and parameters
            advanced_settings: Dict with advanced simulation parameters
            max_time_hours: Maximum simulation time in hours
            
        Returns:
            List of parameter lines for disrealnew.c
        """
        # Extract curing conditions
        initial_temp = curing_conditions.get('initial_temperature_celsius', 25.0)
        thermal_mode = curing_conditions.get('thermal_mode', 'isothermal')
        moisture_mode = curing_conditions.get('moisture_mode', 'sealed')
        
        # Map thermal mode to Adiaflag
        if thermal_mode == 'isothermal':
            adiaflag = 0
        elif thermal_mode == 'adiabatic':
            adiaflag = 1
        else:  # temperature_profile
            # For temperature profile, use isothermal flag but temperature will be handled by profile
            adiaflag = 0  # Could be 1 depending on profile requirements
            
            # Generate temperature profile CSV file if profile data is provided
            temperature_profile_data = curing_conditions.get('temperature_profile_data')
            if temperature_profile_data and operation_name:
                # Create operation directory to store the temperature profile file
                operation_dir = str(self.operations_dir / operation_name)
                os.makedirs(operation_dir, exist_ok=True)
                self._generate_temperature_profile_csv(temperature_profile_data, operation_dir)
        
        # Map moisture mode to Sealed flag  
        sealed_flag = 1 if moisture_mode == 'sealed' else 0
        
        # Process time calibration settings
        if time_calibration_settings:
            calibration_mode = time_calibration_settings.get('mode', 'knudsen')  # Changed from 'calibration_mode' to 'mode'
            calibration_value = time_calibration_settings.get('data_file')  # Changed from 'calibration_value' to 'data_file'
            time_conversion_factor = time_calibration_settings.get('time_conversion_factor', 0.00045)
            
            # Map calibration mode to TimeCalibrationMethod parameter
            if calibration_mode == 'knudsen' or calibration_mode == 'knudsen_parabolic':
                time_calibration_method = 0
                beta_value = time_conversion_factor
                cal_filename = "none"  # Use "none" instead of empty string to avoid NULL pointer on Windows
            elif calibration_mode == 'calorimetry':
                time_calibration_method = 1
                beta_value = time_conversion_factor  # Keep default for reference
                cal_filename = calibration_value if calibration_value else ""
            elif calibration_mode == 'chemical_shrinkage':
                time_calibration_method = 2
                beta_value = time_conversion_factor  # Keep default for reference
                cal_filename = calibration_value if calibration_value else ""
            else:
                # Default to Knudsen parabolic
                time_calibration_method = 0
                beta_value = 0.00045
                cal_filename = ""
        else:
            # Default values
            time_calibration_method = 0
            beta_value = 0.00045
            cal_filename = ""
        
        # Process advanced settings with defaults
        if advanced_settings:
            random_seed = advanced_settings.get('random_seed', -12345)
            c3a_fraction = advanced_settings.get('c3a_fraction', 0.0)
            csh_seeds = advanced_settings.get('csh_seeds', 0.0)
            alpha_max = advanced_settings.get('alpha_max', 1.0)
            e_act_cement = advanced_settings.get('e_act_cement', 40.0)
            e_act_pozzolan = advanced_settings.get('e_act_pozzolan', 83.1)
            e_act_slag = advanced_settings.get('e_act_slag', 50.0)
            burn_frequency = advanced_settings.get('burn_frequency', 1.0)
            setting_frequency = advanced_settings.get('setting_frequency', 0.25)
            physical_frequency = advanced_settings.get('physical_frequency', 2.0)
            movie_frequency = advanced_settings.get('movie_frequency', 72.0)
            save_interval_hours = advanced_settings.get('save_interval_hours', 72.0)
            csh2_flag = advanced_settings.get('csh2_flag', 1)
            ch_flag = advanced_settings.get('ch_flag', 1)
            ph_active = advanced_settings.get('ph_active', 1)
        else:
            # Default values
            random_seed = -12345
            c3a_fraction = 0.0
            csh_seeds = 0.0
            alpha_max = 1.0
            e_act_cement = 40.0
            e_act_pozzolan = 83.1
            e_act_slag = 50.0
            burn_frequency = 1.0
            setting_frequency = 0.25
            physical_frequency = 2.0
            movie_frequency = 72.0
            save_interval_hours = 72.0
            csh2_flag = 1
            ch_flag = 1
            ph_active = 1
        
        # Generate UI parameters in correct order according to disrealnew_input_after_parameters.txt
        ui_parameters = [
            # Basic simulation setup
            f"Iseed,{random_seed}",
            "Micdir,./",
            f"Fileroot,{microstructure_name}.img", 
            f"Pimgfile,{microstructure_name}.pimg",
            f"Oc3afrac,{c3a_fraction}",
            f"Csh_seeds,{csh_seeds}",
            f"End_time,{max_time_hours / 24.0:.1f}",
            "Place_crack,n",
            "Crackwidth,0",
            "Cracktime,0.0", 
            "Crackorient,0",
            "Customize_times,n",
            f"Outtimefreq,{save_interval_hours}",
            
            # NOTE: Onevoxelbias parameters are inserted here by caller
            
            # Thermal conditions (curing conditions integrated)
            f"Temp_0,{initial_temp}",
            f"Adiaflag,{adiaflag}",
            f"T_ambient,{initial_temp}",  # Use same as initial temperature
            "U_coeff,0.0",
            f"E_act,{e_act_cement}",
            f"E_act_pozz,{e_act_pozzolan}", 
            f"E_act_slag,{e_act_slag}",
            f"TimeCalibrationMethod,{time_calibration_method}",
            f"Beta,{beta_value}",
            f"Calfilename,{cal_filename}",
            f"DataMeasuredAtTemperature,{initial_temp}",
            f"Alpha_max,{alpha_max}",
            
            # Moisture conditions (curing conditions integrated)
            f"Sealed,{sealed_flag}",
            
            # Output and timing controls
            f"Burntimefreq,{burn_frequency}",
            f"Settimefreq,{setting_frequency}",
            f"Phydtimefreq,{physical_frequency}",
            "Mass_agg,0.0",  # Will be updated from microstructure if needed
            f"Temp_0_agg,{initial_temp}",
            "U_coeff_agg,0.0",
            f"Csh2flag,{csh2_flag}", 
            f"Chflag,{ch_flag}",
            f"MovieFrameFreq,{movie_frequency}",
            f"PHactive,{ph_active}"
        ]
        
        return ui_parameters
    
    def _extract_psd_parameters(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract PSD parameters from material data."""
        psd_params = {}
        
        # Extract all PSD-related fields
        psd_fields = [
            'psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_exponent',
            'psd_custom_points', 'psd_median', 'psd_spread'
        ]
        
        for field in psd_fields:
            if field in material_data and material_data[field] is not None:
                psd_params[field] = material_data[field]
        
        return psd_params
    
    def _dict_to_psd_parameters(self, psd_dict: Dict[str, Any]) -> PSDParameters:
        """Convert dictionary to PSDParameters object."""
        psd_mode = psd_dict.get('psd_mode', 'log_normal')
        
        # Map string to enum
        psd_type_map = {
            'rosin_rammler': PSDType.ROSIN_RAMMLER,
            'log_normal': PSDType.LOG_NORMAL,
            'fuller_thompson': PSDType.FULLER_THOMPSON,
            'fuller': PSDType.FULLER_THOMPSON,
            'custom': PSDType.CUSTOM
        }
        
        psd_type = psd_type_map.get(psd_mode, PSDType.LOG_NORMAL)
        
        # Parse custom points if present
        custom_points = None
        if psd_dict.get('psd_custom_points'):
            try:
                import json
                points_data = json.loads(psd_dict['psd_custom_points'])
                custom_points = [(p[0], p[1]) for p in points_data]
            except:
                custom_points = None
        
        return PSDParameters(
            psd_type=psd_type,
            d50=psd_dict.get('psd_d50'),
            n=psd_dict.get('psd_n'),
            dmax=psd_dict.get('psd_dmax'),
            median=psd_dict.get('psd_median'),
            sigma=psd_dict.get('psd_spread'),
            exponent=psd_dict.get('psd_exponent'),
            custom_points=custom_points
        )
    
    def _calculate_material_bias(self, material: MicrostructureMaterialInfo,
                               discrete_psd: DiscreteDistribution,
                               quantized_diameters: List[float]) -> OneVoxelBiasResult:
        """Calculate bias for a single material."""
        if len(quantized_diameters) < 2:
            # Fallback quantized diameters
            quantized_diameters = [1.0, 2.0]
        
        d0 = quantized_diameters[0]
        d1 = quantized_diameters[1]
        cutoff = (d0 + d1) / 2.0
        
        # Find cutoff index
        cutoff_reached = False
        upperbin = 0
        
        for i, diameter in enumerate(discrete_psd.diameters):
            if diameter > cutoff:
                cutoff_reached = True
                upperbin = i
                break
        
        if not cutoff_reached:
            upperbin = len(discrete_psd.diameters) - 1
        
        # Calculate bias using OneVoxelBias algorithm
        bias = 1.0
        
        if upperbin > 1:
            # Build cumulative distribution
            cumulative = [0.0] * len(discrete_psd.mass_fractions)
            cumulative[0] = discrete_psd.mass_fractions[0]
            
            for i in range(1, upperbin + 1):
                cumulative[i] = cumulative[i-1] + discrete_psd.mass_fractions[i]
            
            # Normalize up to cutoff
            cutoff_cumulative = cumulative[upperbin]
            if cutoff_cumulative > 0:
                for i in range(upperbin + 1):
                    cumulative[i] /= cutoff_cumulative
            
            # Volume density function
            vdist = [0.0] * (upperbin + 1)
            for i in range(1, upperbin + 1):
                vdist[i] = cumulative[i] - cumulative[i-1]
            vdist[0] = 0.0
            
            # Integration kernel
            kernel = [0.0] * (upperbin + 1)
            for i in range(1, upperbin + 1):
                kernel[i] = vdist[i] * d0 / discrete_psd.diameters[i]
            
            # Trapezoidal integration - numerator
            bias = 0.0
            for i in range(1, upperbin + 1):
                diameter_diff = discrete_psd.diameters[i] - discrete_psd.diameters[i-1]
                bias += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
            
            # Trapezoidal integration - denominator
            for i in range(1, upperbin + 1):
                kernel[i] = vdist[i]
            
            denom = 0.0
            for i in range(1, upperbin + 1):
                diameter_diff = discrete_psd.diameters[i] - discrete_psd.diameters[i-1]
                denom += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
            
            # Final calculation
            if denom > 0:
                bias /= denom
        
        return OneVoxelBiasResult(
            phase_id=material.phase_id,
            material_name=material.material_name,
            bias_value=bias,
            volume_fraction=material.volume_fraction,
            d0=d0,
            d1=d1,
            cutoff_diameter=cutoff
        )
    
    def list_available_microstructures(self) -> List[str]:
        """List available microstructures with metadata."""
        try:
            if not os.path.exists(self.metadata_dir):
                return []
            
            microstructures = []
            for filename in os.listdir(self.metadata_dir):
                if filename.endswith('_metadata.json'):
                    operation_name = filename.replace('_metadata.json', '')
                    microstructures.append(operation_name)
            
            return sorted(microstructures)
            
        except Exception as e:
            self.logger.error(f"Failed to list microstructures: {e}")
            return []
    
    def get_microstructure_summary(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get summary information about a microstructure."""
        metadata = self.load_microstructure_metadata(operation_name)
        if not metadata:
            return None
        
        return {
            'operation_name': metadata.operation_name,
            'microstructure_file': metadata.microstructure_file,
            'system_size': metadata.system_size,
            'resolution': metadata.resolution,
            'num_materials': len(metadata.materials),
            'materials': [
                {
                    'phase_id': m.phase_id,
                    'name': m.material_name,
                    'type': m.material_type,
                    'volume_fraction': m.volume_fraction
                }
                for m in metadata.materials
            ],
            'generation_timestamp': metadata.generation_timestamp
        }
    
    def _copy_microstructure_files(self, microstructure_name: str, operation_dir: str) -> None:
        """
        Copy microstructure files from source operation to hydration simulation directory.
        
        Args:
            microstructure_name: Name of the source microstructure operation
            operation_dir: Path to the hydration simulation operation directory
        """
        try:
            source_dir = str(self.operations_dir / microstructure_name)

            if not os.path.exists(source_dir):
                raise FileNotFoundError(f"Source microstructure directory not found: {source_dir}")
            
            # Files to copy for hydration simulation
            required_files = [
                f"{microstructure_name}.img",   # Main microstructure file
                f"{microstructure_name}.pimg"   # Phase image file
            ]
            
            # Optional files that may exist
            optional_files = [
                f"{microstructure_name}.c3s",   # C3S phase file
                f"{microstructure_name}.c4f",   # C4AF phase file  
                f"{microstructure_name}.alu",   # Aluminate phase file
                f"{microstructure_name}.sil",   # Silica phase file
                f"{microstructure_name}.k2o",   # K2O phase file
                f"{microstructure_name}.img.struct"  # Structure file
            ]
            
            files_copied = 0
            
            # Copy required files
            for filename in required_files:
                source_path = os.path.join(source_dir, filename)
                dest_path = os.path.join(operation_dir, filename)
                
                if os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                    files_copied += 1
                    self.logger.debug(f"Copied required file: {filename}")
                else:
                    raise FileNotFoundError(f"Required microstructure file not found: {source_path}")
            
            # Copy optional files if they exist
            for filename in optional_files:
                source_path = os.path.join(source_dir, filename)
                dest_path = os.path.join(operation_dir, filename)
                
                if os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                    files_copied += 1
                    self.logger.debug(f"Copied optional file: {filename}")
            
            self.logger.info(f"Copied {files_copied} microstructure files from {microstructure_name} to {operation_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to copy microstructure files: {e}")
            raise
    
    def _generate_alkali_files(self, microstructure_name: str, operation_dir: str) -> None:
        """
        Generate alkalichar.dat and alkaliflyash.dat files required by disrealnew.c.
        
        Args:
            microstructure_name: Name of the microstructure operation
            operation_dir: Directory where alkali files should be created
        """
        try:
            # Get cement alkali data from microstructure metadata or use defaults
            alkali_data = self._get_alkali_data_for_microstructure(microstructure_name)
            
            # Generate alkalichar.dat (required file)
            alkalichar_path = os.path.join(operation_dir, "alkalichar.dat")
            with open(alkalichar_path, 'w') as f:
                f.write(f"{alkali_data['cement']['total_sodium']:.3f}\n")     # Totsodium
                f.write(f"{alkali_data['cement']['total_potassium']:.3f}\n")  # Totpotassium  
                f.write(f"{alkali_data['cement']['soluble_sodium']:.3f}\n")   # Rssodium
                f.write(f"{alkali_data['cement']['soluble_potassium']:.3f}\n") # Rspotassium
                f.write(f"{alkali_data['cement']['sodium_hydroxide']:.3f}\n") # Sodiumhydrox
                f.write(f"{alkali_data['cement']['potassium_hydroxide']:.3f}\n") # Potassiumhydrox
            
            # Generate alkaliflyash.dat (optional file - only if fly ash is present)
            if alkali_data.get('fly_ash'):
                alkaliflyash_path = os.path.join(operation_dir, "alkaliflyash.dat")
                with open(alkaliflyash_path, 'w') as f:
                    f.write(f"{alkali_data['fly_ash']['total_sodium']:.3f}\n")     # Totfasodium
                    f.write(f"{alkali_data['fly_ash']['total_potassium']:.3f}\n")  # Totfapotassium
                    f.write(f"{alkali_data['fly_ash']['soluble_sodium']:.3f}\n")   # Rsfasodium
                    f.write(f"{alkali_data['fly_ash']['soluble_potassium']:.3f}\n") # Rsfapotassium
                
                self.logger.info(f"Generated alkali files: alkalichar.dat and alkaliflyash.dat")
            else:
                self.logger.info(f"Generated alkali files: alkalichar.dat only (no fly ash)")
                
        except Exception as e:
            self.logger.error(f"Failed to generate alkali files: {e}")
            raise
    
    def _get_alkali_data_for_microstructure(self, microstructure_name: str) -> Dict[str, Any]:
        """
        Get alkali data for the cement and fly ash materials used in the microstructure.
        
        Args:
            microstructure_name: Name of the microstructure operation
            
        Returns:
            Dict containing alkali data for cement and fly ash (if present)
        """
        try:
            # Try to get metadata for the microstructure
            metadata = self.load_microstructure_metadata(microstructure_name)
            
            if metadata and metadata.materials:
                # Find cement and fly ash materials
                cement_material = None
                flyash_material = None
                
                for material in metadata.materials:
                    if material.material_type == 'cement':
                        cement_material = material
                    elif material.material_type == 'fly_ash':
                        flyash_material = material
                
                # Get alkali data from database
                alkali_data = {'cement': self._get_default_cement_alkali_data()}
                
                if cement_material:
                    cement_alkali = self._get_cement_alkali_from_database(cement_material.material_name)
                    if cement_alkali:
                        alkali_data['cement'] = cement_alkali
                
                if flyash_material:
                    flyash_alkali = self._get_flyash_alkali_from_database(flyash_material.material_name)
                    if flyash_alkali:
                        alkali_data['fly_ash'] = flyash_alkali
                
                return alkali_data
            else:
                self.logger.warning(f"No metadata found for microstructure {microstructure_name}, using default alkali data")
                return {'cement': self._get_default_cement_alkali_data()}
                
        except Exception as e:
            self.logger.error(f"Failed to get alkali data for {microstructure_name}: {e}")
            self.logger.warning("Using default alkali data")
            return {'cement': self._get_default_cement_alkali_data()}
    
    def _get_cement_alkali_from_database(self, cement_name: str) -> Optional[Dict[str, float]]:
        """Get alkali data for a specific cement from the database."""
        try:
            from app.services.service_container import get_service_container
            service_container = get_service_container()
            
            with service_container.database_service.get_read_only_session() as session:
                from app.models.cement import Cement
                cement = session.query(Cement).filter_by(name=cement_name).first()
                
                if cement and cement.alkali_file:
                    # Map alkali_file reference to actual values
                    return self._map_alkali_file_to_values(cement.alkali_file)
                else:
                    self.logger.warning(f"No alkali data found for cement {cement_name}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to get cement alkali data from database: {e}")
            return None
    
    def _get_flyash_alkali_from_database(self, flyash_name: str) -> Optional[Dict[str, float]]:
        """Get alkali data for a specific fly ash from the database."""
        try:
            from app.services.service_container import get_service_container
            service_container = get_service_container()
            
            with service_container.database_service.get_read_only_session() as session:
                from app.models.fly_ash import FlyAsh
                flyash = session.query(FlyAsh).filter_by(name=flyash_name).first()
                
                if flyash and hasattr(flyash, 'alkali_file') and flyash.alkali_file:
                    # Map alkali_file reference to actual values  
                    return self._map_flyash_alkali_file_to_values(flyash.alkali_file)
                else:
                    # Use default fly ash alkali values
                    return self._get_default_flyash_alkali_data()
                    
        except Exception as e:
            self.logger.error(f"Failed to get fly ash alkali data from database: {e}")
            return self._get_default_flyash_alkali_data()
    
    def _map_alkali_file_to_values(self, alkali_file: str) -> Dict[str, float]:
        """
        Map cement alkali_file reference to actual alkali values.
        
        This would ideally be loaded from a lookup table or configuration file.
        For now, using the example values from the existing alkali files.
        """
        # Default mapping based on common alkali file references
        # These values should eventually come from a proper lookup table
        alkali_mappings = {
            'alkalicem116': {
                'total_sodium': 0.191,
                'total_potassium': 0.508, 
                'soluble_sodium': 0.033,
                'soluble_potassium': 0.250,
                'sodium_hydroxide': 0.000,
                'potassium_hydroxide': 0.000
            },
            'alkalicem141': {
                'total_sodium': 0.150,
                'total_potassium': 0.620,
                'soluble_sodium': 0.025,
                'soluble_potassium': 0.280,
                'sodium_hydroxide': 0.000,
                'potassium_hydroxide': 0.000
            },
            'lowalkali': {
                'total_sodium': 0.100,
                'total_potassium': 0.300,
                'soluble_sodium': 0.020,
                'soluble_potassium': 0.150,
                'sodium_hydroxide': 0.000,
                'potassium_hydroxide': 0.000
            }
        }
        
        if alkali_file in alkali_mappings:
            return alkali_mappings[alkali_file]
        else:
            self.logger.warning(f"Unknown alkali file reference: {alkali_file}, using default")
            return self._get_default_cement_alkali_data()
    
    def _map_flyash_alkali_file_to_values(self, alkali_file: str) -> Dict[str, float]:
        """Map fly ash alkali_file reference to actual alkali values."""
        # Default fly ash alkali mappings
        flyash_alkali_mappings = {
            'alkalifa1': {
                'total_sodium': 0.300,
                'total_potassium': 1.060,
                'soluble_sodium': 0.024,
                'soluble_potassium': 0.039
            },
            'lowalkaliFA': {
                'total_sodium': 0.200,
                'total_potassium': 0.800,
                'soluble_sodium': 0.015,
                'soluble_potassium': 0.025
            }
        }
        
        if alkali_file in flyash_alkali_mappings:
            return flyash_alkali_mappings[alkali_file]
        else:
            self.logger.warning(f"Unknown fly ash alkali file reference: {alkali_file}, using default")
            return self._get_default_flyash_alkali_data()
    
    def _get_default_cement_alkali_data(self) -> Dict[str, float]:
        """Get default cement alkali data when no specific data is available."""
        return {
            'total_sodium': 0.191,
            'total_potassium': 0.508,
            'soluble_sodium': 0.033,
            'soluble_potassium': 0.250,
            'sodium_hydroxide': 0.000,
            'potassium_hydroxide': 0.000
        }
    
    def _get_default_flyash_alkali_data(self) -> Dict[str, float]:
        """Get default fly ash alkali data when no specific data is available."""
        return {
            'total_sodium': 0.300,
            'total_potassium': 1.060,
            'soluble_sodium': 0.024,
            'soluble_potassium': 0.039
        }
    
    def _generate_slag_file(self, operation_dir: str) -> None:
        """
        Generate slagchar.dat file required by disrealnew.c.
        
        This file contains slag characteristics including specific gravities,
        molar volumes, and other properties needed for slag hydration modeling.
        
        Args:
            operation_dir: Directory where slag file should be created
        """
        try:
            # Get default slag characteristics
            # These values are based on standard slag properties from the existing files
            slag_data = self._get_default_slag_data()
            
            # Generate slagchar.dat file
            slagchar_path = os.path.join(operation_dir, "slagchar.dat")
            with open(slagchar_path, 'w') as f:
                f.write(f"{slag_data['value1']:.1f}\n")        # First value (not used in C code)
                f.write(f"{slag_data['value2']:.1f}\n")        # Second value (not used in C code)
                f.write(f"{slag_data['slag_specific_gravity']:.3f}\n")     # Specgrav[SLAG]
                f.write(f"{slag_data['slagcsh_specific_gravity']:.3f}\n")  # Specgrav[SLAGCSH]
                f.write(f"{slag_data['slag_molar_volume']:.3f}\n")         # Molarv[SLAG]
                f.write(f"{slag_data['slagcsh_molar_volume']:.3f}\n")      # Molarv[SLAGCSH]
                f.write(f"{slag_data['slag_casi_ratio']:.3f}\n")           # Slagcasi
                f.write(f"{slag_data['slag_hyd_casi_ratio']:.3f}\n")       # Slaghydcasi
                f.write(f"{slag_data['si_per_slag']:.3f}\n")               # Siperslag
                f.write(f"{slag_data['water_coefficient']:.3f}\n")         # Water coefficient
                f.write(f"{slag_data['additional_param1']:.3f}\n")         # Additional parameter 1
                f.write(f"{slag_data['additional_param2']:.3f}\n")         # Additional parameter 2
            
            self.logger.info(f"Generated slag characteristics file: slagchar.dat")
            
        except Exception as e:
            self.logger.error(f"Failed to generate slag file: {e}")
            raise
    
    def _get_default_slag_data(self) -> Dict[str, float]:
        """
        Get default slag characteristics data.
        
        These values are based on typical slag properties and should eventually
        be configurable or retrieved from a database if slag materials are used.
        """
        return {
            'value1': 2492.4,                    # First value (unused in C code)
            'value2': 4030.8,                    # Second value (unused in C code)
            'slag_specific_gravity': 2.870,      # Specific gravity of slag
            'slagcsh_specific_gravity': 2.500,   # Specific gravity of slag CSH
            'slag_molar_volume': 868.430,        # Molar volume of slag (cm³/mol)
            'slagcsh_molar_volume': 1612.320,    # Molar volume of slag CSH (cm³/mol)
            'slag_casi_ratio': 0.970,            # CaSi ratio in slag
            'slag_hyd_casi_ratio': 1.300,        # CaSi ratio in hydrated slag
            'si_per_slag': 17.000,               # Silicon per slag unit
            'water_coefficient': 4.000,          # Water coefficient for CSH calculation
            'additional_param1': 0.000,          # Additional parameter 1
            'additional_param2': 1.000           # Additional parameter 2
        }
    
    def _generate_temperature_profile_csv(self, temperature_profile_data: List[Tuple[float, float]], operation_dir: str) -> None:
        """
        Generate temperature_profile.csv file for disrealnew.c.
        
        The file format required by disrealnew.c is:
        time_start,time_finish,temperature_start,temperature_finish
        
        Args:
            temperature_profile_data: List of (time_hours, temperature_celsius) tuples
            operation_dir: Directory where the CSV file should be created
        """
        try:
            csv_file_path = os.path.join(operation_dir, "temperature_profile.csv")
            
            with open(csv_file_path, 'w') as f:
                # Convert point data to interval data required by disrealnew.c
                for i in range(len(temperature_profile_data) - 1):
                    time_start = temperature_profile_data[i][0]
                    temp_start = temperature_profile_data[i][1]
                    time_finish = temperature_profile_data[i + 1][0]
                    temp_finish = temperature_profile_data[i + 1][1]
                    
                    f.write(f"{time_start:.1f},{time_finish:.1f},{temp_start:.1f},{temp_finish:.1f}\n")
            
            self.logger.info(f"Generated temperature profile CSV with {len(temperature_profile_data) - 1} intervals: {csv_file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate temperature profile CSV: {e}")
            raise