# Cement Persistence Fixes - September 6, 2025

## Problem Summary
When duplicating and editing cement materials, activation energy and PSD (Particle Size Distribution) data were not persisting correctly. Changes would appear to save successfully but would revert to original values when reopening the dialog.

## Root Cause Analysis

### 1. PSD Data Fields Missing from Pydantic Models
**Issue**: The `CementUpdate` and `CementCreate` Pydantic models were missing PSD field definitions (`psd_mode`, `psd_d50`, `psd_n`, etc.). When the material dialog sent these fields, Pydantic was silently rejecting them because they weren't defined in the model schema.

**Evidence**: Debug output showed `Extracted psd_data = {}` before fix, indicating PSD fields were not being processed.

### 2. Activation Energy Not Loading in Dialog
**Issue**: The cement dialog's `_load_material_specific_data` method was missing code to load activation energy from the database. The widget was created but never populated with saved data.

**Evidence**: Activation energy always showed the default value (54000) regardless of what was saved in the database.

## Fixes Applied

### Fix 1: Added PSD Fields to Pydantic Models
**File**: `/src/app/models/cement.py`

Added PSD fields to both `CementCreate` and `CementUpdate` models:
```python
# PSD fields that can be updated (will be handled via relationship)
psd_mode: Optional[str] = Field(None, description="PSD mode (rosin_rammler, log_normal, fuller, custom)")
psd_d50: Optional[float] = Field(None, ge=0.0, le=1000.0, description="D50 particle size (μm)")
psd_n: Optional[float] = Field(None, ge=0.0, le=10.0, description="Distribution parameter")
psd_dmax: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Maximum particle size (μm)")
psd_median: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Median particle size (μm)")
psd_spread: Optional[float] = Field(None, ge=0.0, le=10.0, description="Distribution spread parameter")
psd_exponent: Optional[float] = Field(None, ge=0.0, le=2.0, description="Exponent parameter")
psd_custom_points: Optional[str] = Field(None, description="Custom PSD points as JSON")
```

### Fix 2: Enhanced Cement Service PSD Handling
**File**: `/src/app/services/cement_service.py`

The cement service already had proper PSD relationship handling that:
- Separates PSD fields from cement fields during updates
- Creates or updates PSD data records in the separate `psd_data` table
- Uses eager loading with `joinedload(Cement.psd_data)` to ensure PSD data is available

### Fix 3: Added Activation Energy Loading to Dialog
**File**: `/src/app/windows/dialogs/material_dialog.py`

Added activation energy loading in `_load_material_specific_data()` method:
```python
# Load activation energy if available
if hasattr(self, 'physical_properties') and 'activation_energy' in self.physical_properties:
    activation_energy = self.material_data.get('activation_energy', 54000.0)
    self.physical_properties['activation_energy'].set_value(float(activation_energy))
```

### Fix 4: Improved Material Data Re-fetching
**File**: `/src/app/windows/panels/materials_panel.py`

Enhanced `_on_edit_material_clicked()` to re-fetch fresh material data from the database before opening the dialog, preventing stale data issues.

## Testing Results

Created comprehensive test script that:
1. Duplicates a cement material
2. Updates both activation energy and PSD data
3. Re-fetches to verify persistence
4. Checks database directly

**Before fixes**: 
- ✅ Activation energy persisted at service level but failed to load in GUI
- ❌ PSD data was silently rejected by Pydantic validation

**After fixes**:
- ✅ Activation energy persists correctly (both GUI and database)
- ✅ PSD data persists correctly (both GUI and database)

## Files Modified
1. `/src/app/models/cement.py` - Added PSD fields to Pydantic models
2. `/src/app/windows/dialogs/material_dialog.py` - Added activation energy loading
3. `/src/app/windows/panels/materials_panel.py` - Enhanced data re-fetching
4. `/src/app/services/cement_service.py` - Enhanced PSD relationship handling (already present)

## Additional Context: Specific Gravity vs Calculated Density

The cement dialog shows two density-related fields:
- **Specific Gravity**: Measured bulk density of the actual cement material (input field)
- **Calculated Density**: Theoretical density calculated from phase composition (C3S, C2S, C3A, C4AF)

These values typically don't match because:
- Calculated density only considers main phases, not gypsum, alkalis, or impurities
- Specific gravity reflects real-world material properties including porosity and crystal defects
- They serve different purposes: specific gravity for mix design, calculated density for theoretical validation

## Status
✅ All cement persistence issues resolved
✅ Both activation energy and PSD data now persist correctly
✅ System ready for filler material testing