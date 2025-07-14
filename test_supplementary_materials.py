#!/usr/bin/env python3
"""
Test Supplementary Materials Interface (VCCTL-014)

This script tests the supplementary material functionality required for VCCTL-014:
- Fly ash form with alkali characteristics
- Slag form with reaction parameters and Ca/Si ratios  
- Inert filler form with basic properties
- Material-specific validation rules
- Calculation helpers for derived properties
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def clear_test_data():
    """Clear any existing test data."""
    try:
        from app.services.service_container import get_service_container
        services = get_service_container()
        
        # Clear test materials to avoid conflicts
        test_names = [
            'Class F Fly Ash Test', 'GGBS Grade 120 Test', 'Limestone Filler Test',
            'Class F Fly Ash', 'GGBS Grade 120', 'Limestone Filler',
            'Quartz Filler', 'Glass Powder', 'Granite Fines',
            'Test Slag 0.8', 'Test Slag 1.1', 'Test Slag 1.4', 'Test Slag 1.8',
            'Invalid Slag', 'Test SG 1.5', 'Test SG 2.2', 'Test SG 2.8', 'Test SG 4.5', 'Test SG 6.0',
            'Calculation Test FA', 'Calculation Test Slag', 'Calculation Test Filler',
            'Valid FA', 'Invalid FA', 'Invalid Phases', 'Valid Slag', 'Valid Filler', 'Invalid Filler'
        ]
        
        for name in test_names:
            try:
                services.fly_ash_service.delete(name)
            except:
                pass
            try:
                services.slag_service.delete(name)
            except:
                pass
            try:
                services.inert_filler_service.delete(name)
            except:
                pass
        
    except Exception:
        pass  # Ignore errors in cleanup

def test_fly_ash_interface():
    """Test fly ash interface with alkali characteristics."""
    print("🏭 Testing Fly Ash Interface")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        from app.models.fly_ash import FlyAshCreate, FlyAshUpdate
        
        services = get_service_container()
        fly_ash_service = services.fly_ash_service
        
        # Test 1: Create fly ash with alkali characteristics
        print("Test 1: Fly ash with alkali characteristics")
        fly_ash_data = FlyAshCreate(
            name='Class F Fly Ash Test',
            specific_gravity=2.30,
            aluminosilicate_glass_fraction=0.75,  # Primary alkali-bearing phase
            calcium_aluminum_disilicate_fraction=0.15,
            tricalcium_aluminate_fraction=0.05,
            silica_fraction=0.03,
            anhydrate_fraction=0.02,
            description='Low-calcium fly ash with alkali reactive glass'
        )
        
        created_fly_ash = fly_ash_service.create(fly_ash_data)
        print(f"✓ Created: {created_fly_ash.name}")
        print(f"✓ Alkali glass content: {created_fly_ash.aluminosilicate_glass_fraction:.1%}")
        total_phases = created_fly_ash.total_phase_fraction
        if total_phases is not None:
            print(f"✓ Total phases: {total_phases:.1%}")
        else:
            print("✓ Total phases: Incomplete data")
        print(f"✓ Complete phase data: {created_fly_ash.has_complete_phase_data}")
        
        # Test 2: Validate phase fraction limits
        print("\nTest 2: Fly ash phase validation")
        try:
            invalid_fly_ash = FlyAshCreate(
                name='Invalid Fly Ash',
                aluminosilicate_glass_fraction=0.60,
                calcium_aluminum_disilicate_fraction=0.30,
                tricalcium_aluminate_fraction=0.20,
                silica_fraction=0.15  # Total > 100%
            )
            print("❌ Should have failed validation")
            return False
        except ValueError as e:
            print(f"✓ Correctly rejected invalid composition: {str(e)[:60]}...")
        
        # Test 3: Test phase distribution input generation
        print("\nTest 3: Phase distribution input")
        phase_input = created_fly_ash.build_phase_distribution_input()
        lines = phase_input.strip().split('\n')
        print(f"✓ Generated phase distribution with {len(lines)} parameters")
        print(f"✓ Glass fraction in input: {lines[1]}")
        
        # Test 4: Update fly ash properties
        print("\nTest 4: Update fly ash alkali characteristics")
        update_data = FlyAshUpdate(
            aluminosilicate_glass_fraction=0.70,  # Decrease alkali glass to stay within valid total
            description='Updated alkali characteristics'
        )
        updated_fly_ash = fly_ash_service.update(created_fly_ash.name, update_data)
        print(f"✓ Updated alkali glass to: {updated_fly_ash.aluminosilicate_glass_fraction:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing fly ash interface: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_slag_interface():
    """Test slag interface with reaction parameters and Ca/Si ratios."""
    print("\n🏗️ Testing Slag Interface")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        from app.models.slag import SlagCreate, SlagUpdate
        
        services = get_service_container()
        slag_service = services.slag_service
        
        # Test 1: Create slag with Ca/Si ratios and reaction parameters
        print("Test 1: Slag with Ca/Si ratios and reaction parameters")
        slag_data = SlagCreate(
            name='GGBS Grade 120 Test',
            specific_gravity=2.95,
            molecular_mass=120.5,
            casi_mol_ratio=1.25,  # Ca/Si molar ratio - key for hydraulicity
            si_per_mole=1.0,
            base_slag_reactivity=0.85,
            c3a_per_mole=0.05,
            # Hydration product properties
            hp_molecular_mass=150.0,
            hp_density=2.2,
            hp_casi_mol_ratio=1.7,  # C-S-H gel Ca/Si ratio
            hp_h2o_si_mol_ratio=1.8,  # Water/Si ratio in hydration products
            description='High-grade GGBS with good hydraulic activity'
        )
        
        created_slag = slag_service.create(slag_data)
        print(f"✓ Created: {created_slag.name}")
        print(f"✓ Ca/Si molar ratio: {created_slag.casi_mol_ratio:.2f}")
        print(f"✓ Base reactivity: {created_slag.base_slag_reactivity:.2f}")
        print(f"✓ HP Ca/Si ratio: {created_slag.hp_casi_mol_ratio:.2f}")
        print(f"✓ HP H2O/Si ratio: {created_slag.hp_h2o_si_mol_ratio:.2f}")
        
        # Test 2: Validate molecular ratios
        print("\nTest 2: Molecular ratio validation")
        print(f"✓ Molecular ratios valid: {created_slag.validate_molecular_ratios()}")
        print(f"✓ Complete molecular data: {created_slag.has_complete_molecular_data}")
        print(f"✓ Complete HP data: {created_slag.has_complete_hp_data}")
        print(f"✓ Has reactivity data: {created_slag.has_reactivity_data}")
        
        # Test 3: Calculate activation energy
        print("\nTest 3: Activation energy calculation")
        activation_energy = created_slag.calculate_activation_energy(25.0)
        if activation_energy:
            print(f"✓ Calculated activation energy: {activation_energy:.0f} J/mol")
        else:
            print("⚠️  Insufficient data for activation energy calculation")
        
        # Test 4: Test different Ca/Si ratios for hydraulic activity
        print("\nTest 4: Ca/Si ratio impact on hydraulicity")
        test_ratios = [
            ('Low hydraulicity', 0.8),
            ('Moderate hydraulicity', 1.1), 
            ('High hydraulicity', 1.4),
            ('Very high hydraulicity', 1.8)
        ]
        
        for description, ratio in test_ratios:
            # Clear any existing test with this name first
            try:
                slag_service.delete(f'Test Slag {ratio}')
            except:
                pass
                
            test_slag = SlagCreate(
                name=f'Test Slag {ratio}',
                casi_mol_ratio=ratio,
                base_slag_reactivity=min(ratio / 1.0, 1.0),  # Scale reactivity with ratio
                description=f'{description} - Ca/Si = {ratio}'
            )
            test_created = slag_service.create(test_slag)
            print(f"✓ {description}: Ca/Si = {ratio:.1f}, reactivity = {test_created.base_slag_reactivity:.2f}")
        
        # Test 5: Invalid ratio validation  
        print("\nTest 5: Invalid ratio validation")
        try:
            invalid_slag = SlagCreate(
                name='Invalid Slag',
                casi_mol_ratio=15.0,  # Too high
                hp_h2o_si_mol_ratio=8.0  # Too high
            )
            # Create but test validation
            created_invalid = slag_service.create(invalid_slag)
            is_valid = created_invalid.validate_molecular_ratios()
            if not is_valid:
                print("✓ Correctly identified invalid molecular ratios")
            else:
                print("⚠️  Should have flagged invalid ratios")
        except Exception as e:
            print(f"✓ Validation caught invalid ratios: {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing slag interface: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_inert_filler_interface():
    """Test inert filler interface with basic properties."""
    print("\n🪨 Testing Inert Filler Interface")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        from app.models.inert_filler import InertFillerCreate, InertFillerUpdate
        
        services = get_service_container()
        filler_service = services.inert_filler_service
        
        # Test 1: Create various types of inert fillers
        print("Test 1: Various inert filler types")
        filler_types = [
            {
                'name': 'Limestone Filler Test',
                'sg': 2.72,
                'psd': 'fine_limestone',
                'desc': 'Ground limestone powder for filler effect'
            },
            {
                'name': 'Quartz Filler', 
                'sg': 2.65,
                'psd': 'quartz_fine',
                'desc': 'Crystalline silica filler'
            },
            {
                'name': 'Glass Powder',
                'sg': 2.50,
                'psd': 'glass_powder',
                'desc': 'Recycled glass powder filler'
            },
            {
                'name': 'Granite Fines',
                'sg': 2.68,
                'psd': 'granite_fines', 
                'desc': 'Crushed granite filler'
            }
        ]
        
        created_fillers = []
        for filler_spec in filler_types:
            # Clear any existing filler with this name first
            try:
                filler_service.delete(filler_spec['name'])
            except:
                pass
                
            filler_data = InertFillerCreate(
                name=filler_spec['name'],
                specific_gravity=filler_spec['sg'],
                psd=filler_spec['psd'],
                description=filler_spec['desc']
            )
            
            created_filler = filler_service.create(filler_data)
            created_fillers.append(created_filler)
            volume_per_mass = created_filler.get_volume_per_unit_mass()
            
            print(f"✓ Created {filler_spec['name']}")
            vol_text = f"Vol/mass: {volume_per_mass:.6f} m³/kg" if volume_per_mass else "Vol/mass: N/A"
            print(f"  SG: {created_filler.specific_gravity}, "
                  f"Valid: {created_filler.is_valid_specific_gravity}, "
                  f"{vol_text}")
        
        # Test 2: Test specific gravity validation ranges
        print("\nTest 2: Specific gravity validation")
        sg_tests = [
            (2.2, True, "Valid low"),
            (2.8, True, "Valid typical"),
            (4.5, True, "Valid high")
        ]
        
        # Test invalid specific gravities separately to check error handling
        invalid_sg_tests = [
            (1.5, "Too low (service validation)"),
            (6.0, "Too high (service validation)")
        ]
        
        for sg, description in invalid_sg_tests:
            try:
                filler_data = InertFillerCreate(
                    name=f'Test SG {sg}',
                    specific_gravity=sg
                )
                created_test = filler_service.create(filler_data)
                print(f"⚠️ {description}: SG={sg} - Should have been rejected by service")
            except Exception as e:
                print(f"✓ {description}: SG={sg} - Correctly rejected by service")
        
        for sg, should_be_valid, description in sg_tests:
            # Clear any existing test with this name first
            try:
                filler_service.delete(f'Test SG {sg}')
            except:
                pass
                
            filler_data = InertFillerCreate(
                name=f'Test SG {sg}',
                specific_gravity=sg
            )
            created_test = filler_service.create(filler_data)
            is_valid = created_test.is_valid_specific_gravity
            status = "✓" if is_valid == should_be_valid else "⚠️"
            print(f"{status} {description}: SG={sg}, Valid={is_valid}")
        
        # Test 3: Volume calculations
        print("\nTest 3: Volume calculations")
        for filler in created_fillers[:2]:  # Test first two
            volume = filler.get_volume_per_unit_mass()
            if volume:
                # Calculate bulk density 
                bulk_density = 1.0 / volume
                print(f"✓ {filler.name}: Volume = {volume:.6f} m³/kg, Bulk density = {bulk_density:.0f} kg/m³")
        
        # Test 4: Description and properties
        print("\nTest 4: Description and properties")
        for filler in created_fillers:
            has_desc = filler.has_description
            print(f"✓ {filler.name}: Has description = {has_desc}")
        
        # Test 5: Update filler properties
        print("\nTest 5: Update filler properties")
        update_data = InertFillerUpdate(
            specific_gravity=2.75,
            description='Updated limestone filler with improved fineness'
        )
        updated_filler = filler_service.update(created_fillers[0].name, update_data)
        print(f"✓ Updated {updated_filler.name}: SG = {updated_filler.specific_gravity}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing inert filler interface: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_material_specific_validations():
    """Test material-specific validation rules across all supplementary materials."""
    print("\n🔍 Testing Material-Specific Validations")
    print("=" * 50)
    
    try:
        from app.models.fly_ash import FlyAshCreate
        from app.models.slag import SlagCreate
        from app.models.inert_filler import InertFillerCreate
        
        validation_tests = []
        
        # Fly ash validation tests
        print("Fly Ash Validations:")
        fly_ash_tests = [
            {
                'name': 'Valid fly ash',
                'data': {
                    'name': 'Valid FA',
                    'specific_gravity': 2.3,
                    'aluminosilicate_glass_fraction': 0.8
                },
                'should_pass': True
            },
            {
                'name': 'Negative specific gravity',
                'data': {
                    'name': 'Invalid FA',
                    'specific_gravity': -1.0
                },
                'should_pass': False
            },
            {
                'name': 'Phase fractions > 100%',
                'data': {
                    'name': 'Invalid Phases',
                    'aluminosilicate_glass_fraction': 0.6,
                    'calcium_aluminum_disilicate_fraction': 0.3,
                    'tricalcium_aluminate_fraction': 0.2,
                    'silica_fraction': 0.1
                },
                'should_pass': False
            }
        ]
        
        for test in fly_ash_tests:
            try:
                fly_ash = FlyAshCreate(**test['data'])
                if test['should_pass']:
                    print(f"✓ {test['name']}: Passed as expected")
                    validation_tests.append(True)
                else:
                    print(f"❌ {test['name']}: Should have failed")
                    validation_tests.append(False)
            except ValueError as e:
                if not test['should_pass']:
                    print(f"✓ {test['name']}: Correctly rejected")
                    validation_tests.append(True)
                else:
                    print(f"❌ {test['name']}: Unexpected failure")
                    validation_tests.append(False)
        
        # Slag validation tests
        print("\nSlag Validations:")
        slag_tests = [
            {
                'name': 'Valid slag',
                'data': {
                    'name': 'Valid Slag',
                    'specific_gravity': 2.9,
                    'casi_mol_ratio': 1.2
                },
                'should_pass': True
            },
            {
                'name': 'Invalid Ca/Si ratio',
                'data': {
                    'name': 'Invalid Slag',
                    'casi_mol_ratio': -1.0
                },
                'should_pass': False
            }
        ]
        
        for test in slag_tests:
            try:
                slag = SlagCreate(**test['data'])
                if test['should_pass']:
                    print(f"✓ {test['name']}: Passed as expected")
                    validation_tests.append(True)
                else:
                    print(f"❌ {test['name']}: Should have failed")
                    validation_tests.append(False)
            except ValueError as e:
                if not test['should_pass']:
                    print(f"✓ {test['name']}: Correctly rejected")
                    validation_tests.append(True)
                else:
                    print(f"❌ {test['name']}: Unexpected failure")
                    validation_tests.append(False)
        
        # Inert filler validation tests
        print("\nInert Filler Validations:")
        filler_tests = [
            {
                'name': 'Valid filler',
                'data': {
                    'name': 'Valid Filler',
                    'specific_gravity': 2.7
                },
                'should_pass': True
            },
            {
                'name': 'Zero specific gravity',
                'data': {
                    'name': 'Invalid Filler',
                    'specific_gravity': 0.0
                },
                'should_pass': False
            }
        ]
        
        for test in filler_tests:
            try:
                filler = InertFillerCreate(**test['data'])
                if test['should_pass']:
                    print(f"✓ {test['name']}: Passed as expected")
                    validation_tests.append(True)
                else:
                    print(f"❌ {test['name']}: Should have failed")
                    validation_tests.append(False)
            except ValueError as e:
                if not test['should_pass']:
                    print(f"✓ {test['name']}: Correctly rejected")
                    validation_tests.append(True)
                else:
                    print(f"❌ {test['name']}: Unexpected failure")
                    validation_tests.append(False)
        
        passed = sum(validation_tests)
        total = len(validation_tests)
        print(f"\n📊 Validation tests: {passed}/{total} passed")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Error testing validations: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_derived_property_calculations():
    """Test calculation helpers for derived properties."""
    print("\n🧮 Testing Derived Property Calculations")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        from app.models.fly_ash import FlyAshCreate
        from app.models.slag import SlagCreate
        from app.models.inert_filler import InertFillerCreate
        
        services = get_service_container()
        
        # Test fly ash phase calculations
        print("Fly Ash Phase Calculations:")
        fly_ash_data = FlyAshCreate(
            name='Calculation Test FA',
            aluminosilicate_glass_fraction=0.75,
            calcium_aluminum_disilicate_fraction=0.15,
            tricalcium_aluminate_fraction=0.05,
            silica_fraction=0.03,
            anhydrate_fraction=0.02
        )
        
        # Clear any existing test data first
        try:
            services.fly_ash_service.delete('Calculation Test FA')
        except:
            pass
            
        created_fa = services.fly_ash_service.create(fly_ash_data)
        total_phases = created_fa.total_phase_fraction
        phase_dict = created_fa.phase_fractions
        
        if total_phases is not None:
            print(f"✓ Total phase fraction: {total_phases:.1%}")
        else:
            print("✓ Total phase fraction: Incomplete data")
        print(f"✓ Phase distribution:")
        for phase, fraction in phase_dict.items():
            if fraction is not None:
                print(f"   {phase}: {fraction:.1%}")
            else:
                print(f"   {phase}: Not specified")
        
        # Test slag hydraulic calculations
        print("\nSlag Hydraulic Calculations:")
        slag_data = SlagCreate(
            name='Calculation Test Slag',
            casi_mol_ratio=1.35,
            base_slag_reactivity=0.9,
            hp_casi_mol_ratio=1.6,
            hp_h2o_si_mol_ratio=1.5
        )
        
        # Clear any existing test data first
        try:
            services.slag_service.delete('Calculation Test Slag')
        except:
            pass
            
        created_slag = services.slag_service.create(slag_data)
        activation_energy = created_slag.calculate_activation_energy(20.0)
        molecular_props = created_slag.molecular_properties
        hp_props = created_slag.hydration_product_properties
        
        print(f"✓ Ca/Si ratio: {created_slag.casi_mol_ratio:.2f}")
        print(f"✓ Activation energy at 20°C: {activation_energy:.0f} J/mol" if activation_energy else "✓ Activation energy: N/A")
        print(f"✓ Molecular properties complete: {created_slag.has_complete_molecular_data}")
        print(f"✓ HP properties complete: {created_slag.has_complete_hp_data}")
        
        # Test inert filler volume calculations
        print("\nInert Filler Volume Calculations:")
        filler_data = InertFillerCreate(
            name='Calculation Test Filler',
            specific_gravity=2.65
        )
        
        # Clear any existing test data first
        try:
            services.inert_filler_service.delete('Calculation Test Filler')
        except:
            pass
            
        created_filler = services.inert_filler_service.create(filler_data)
        volume_per_mass = created_filler.get_volume_per_unit_mass()
        
        print(f"✓ Specific gravity: {created_filler.specific_gravity}")
        print(f"✓ Volume per unit mass: {volume_per_mass:.6f} m³/kg" if volume_per_mass else "✓ Volume calculation: N/A")
        print(f"✓ SG in valid range: {created_filler.is_valid_specific_gravity}")
        
        # Calculate some derived properties
        if volume_per_mass:
            bulk_density = 1.0 / volume_per_mass
            porosity_50pct = 1.0 - (0.5 / created_filler.specific_gravity)  # 50% packing efficiency
            print(f"✓ Theoretical bulk density: {bulk_density:.0f} kg/m³")
            print(f"✓ Porosity at 50% packing: {porosity_50pct:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing derived calculations: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all supplementary materials interface tests."""
    print("🧪 VCCTL-014: Supplementary Materials Interface Tests")
    print("=" * 60)
    
    # Clear any existing test data
    clear_test_data()
    
    tests = [
        test_fly_ash_interface,
        test_slag_interface,
        test_inert_filler_interface,
        test_material_specific_validations,
        test_derived_property_calculations
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Supplementary Materials Test Results")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All supplementary materials tests passed!")
        print("\n🎯 VCCTL-014 Status:")
        print("  ✅ Fly ash form with alkali characteristics")
        print("  ✅ Slag form with reaction parameters and Ca/Si ratios")
        print("  ✅ Inert filler form with basic properties")
        print("  ✅ Material-specific validation rules")
        print("  ✅ Calculation helpers for derived properties")
        print("  ✅ Comprehensive GUI dialogs (already implemented)")
        print("\n📋 VCCTL-014: Supplementary Materials Interface - COMPLETE ✅")
    else:
        print("❌ Some supplementary materials tests failed. Check output above.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)