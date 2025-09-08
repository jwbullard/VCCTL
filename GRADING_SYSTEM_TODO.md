# Aggregate Grading Data Management System - Implementation Plan

## Phase 1: Backend Infrastructure

### 1.1 Database Schema Enhancement
- [ ] Update `Grading` model to properly store grading curve data
  - Add JSON field for sieve data points `[(size_mm, percent_passing)]`
  - Add reference fields for aggregate association
  - Add user-friendly naming and description fields
  - Add created/modified timestamps
- [ ] Create `GradingService` for CRUD operations
  - Implement save_grading(name, type, sieve_data)
  - Implement get_all_gradings(type=None)
  - Implement get_grading_by_name(name)
  - Implement delete_grading(id)
  - Implement duplicate_grading(id, new_name)
- [ ] Add grading data migration script for existing database

### 1.2 File System Integration
- [ ] Create grading file management utilities
  - Function to write .gdg files to Operations/{operation_name}/
  - Function to read .gdg files and parse sieve data
  - Standard file format (tab-delimited: size\tpercent_passing)
- [ ] Implement grading file path tracking
  - Store relative paths in operation parameters
  - Ensure paths work across different installations

## Phase 2: UI Components Enhancement

### 2.1 Grading Management Dialog
- [ ] Create `GradingManagementDialog` (similar to Mix Design Management)
  - List view of saved gradings with search/filter
  - Show grading name, type (fine/coarse), max size, date
  - Toolbar with Load, Save As, Delete, Duplicate, Export buttons
  - Preview panel showing grading curve graph
- [ ] Add "Manage Gradings" button to Mix Design panel
  - Place near aggregate selection area
  - Opens the management dialog

### 2.2 Enhanced Grading Curve Widget
- [ ] Add "Save as Template" button to GradingCurveWidget
  - Prompts for grading name and description
  - Saves to database via GradingService
- [ ] Add "Load from Template" dropdown
  - Shows saved gradings filtered by type (fine/coarse)
  - Loads sieve data into current widget
- [ ] Add import/export functionality
  - Import from CSV/text files
  - Export to standard formats

## Phase 3: Mix Design Integration

### 3.1 Mix Design Panel Updates
- [ ] Modify aggregate grading buttons behavior
  - Show indicator when grading is set (checkmark icon)
  - Display grading name in tooltip if loaded from template
- [ ] Add grading data to UI parameter capture
  - Include in `_capture_ui_parameters()` method
  - Store as `fine_aggregate_grading_data` and `coarse_aggregate_grading_data`
  - Include grading name/id if loaded from template

### 3.2 Mix Design Storage
- [ ] Update MixDesign model to reference gradings
  - Add `fine_grading_id` foreign key (optional)
  - Add `coarse_grading_id` foreign key (optional)
  - Add `fine_grading_data` JSON field for custom curves
  - Add `coarse_grading_data` JSON field for custom curves
- [ ] Modify mix design save/load operations
  - Save grading references with mix design
  - Restore grading data when loading mix design

## Phase 4: Operation Integration

### 4.1 Microstructure Operation Enhancement
- [ ] Include grading data in operation creation
  - Add grading file paths to stored_ui_parameters
  - Write .gdg files to Operations/{operation_name}/ folder
  - Store both template reference and actual data
- [ ] Update operation display
  - Show grading info in operation details
  - Display "Fine: ASTM C-33, Coarse: #57 Stone" etc.

### 4.2 Lineage Data Flow
- [ ] Implement grading data inheritance
  - Pass grading file paths through operation lineage
  - Microstructure → Hydration → Elastic Moduli
- [ ] Add fallback mechanisms
  - Regenerate .gdg files from stored parameters if missing
  - Handle missing grading data gracefully

## Phase 5: Elastic Moduli Integration

### 5.1 Auto-Population Enhancement
- [ ] Update `_populate_fields_from_hydration()`
  - Extract grading file paths from parent operations
  - Auto-fill grading file entries in elastic moduli form
- [ ] Add grading file validation
  - Check if referenced files exist
  - Provide browse button to locate if missing

### 5.2 Input File Generation
- [ ] Update elastic.in generation
  - Include correct grading file paths
  - Ensure paths are relative to execution directory

## Phase 6: User Experience Polish

### 6.1 Validation and Feedback
- [ ] Add grading curve validation
  - Check for monotonic decreasing percent passing
  - Verify size range appropriate for aggregate type
  - Warn about unusual distributions
- [ ] Provide visual feedback
  - Show grading curve preview in tooltips
  - Highlight when grading is modified vs. template

### 6.2 Default Gradings
- [ ] Pre-populate standard gradings
  - ASTM C-33 fine aggregate limits
  - Common coarse aggregate distributions (#57, #67, etc.)
  - Make these immutable system templates
- [ ] Auto-select appropriate defaults
  - Based on aggregate type selection
  - User can override with custom curves

## Phase 7: Testing and Documentation

### 7.1 Testing
- [ ] Unit tests for GradingService
- [ ] Integration tests for grading data flow
- [ ] UI tests for grading management dialog
- [ ] End-to-end test: Mix → Microstructure → Hydration → Elastic

### 7.2 Documentation
- [ ] Update CLAUDE.md with grading system details
- [ ] Create user guide for grading management
- [ ] Document .gdg file format specification

## Implementation Priority Order:

1. **Critical Path** (Must have for elastic moduli to work):
   - Database schema updates (1.1)
   - Grading file management (1.2)
   - Mix Design parameter capture (3.1)
   - Operation integration (4.1)
   - Elastic moduli auto-population (5.1)

2. **User Experience** (Important for usability):
   - Grading Management Dialog (2.1)
   - Enhanced widget features (2.2)
   - Mix Design storage (3.2)

3. **Polish** (Nice to have):
   - Validation and feedback (6.1)
   - Default gradings (6.2)
   - Complete testing suite (7.1)