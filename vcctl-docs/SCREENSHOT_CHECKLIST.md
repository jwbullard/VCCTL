# VCCTL Documentation Screenshot Checklist

## Storage Location
All screenshots should be saved to: `vcctl-docs/docs/assets/images/screenshots/`

## Naming Convention
Use descriptive kebab-case names: `feature-subfeat-detail.png`

---

## 1. General UI Elements (`screenshots/general/`)

- [x] `main-window-overview.png` - Full VCCTL main window with all panels visible
- [x] `main-menu-bar.png` - Top menu bar (File, Edit, View, etc.)
- [ ] `toolbar-icons.png` - Main toolbar with icons
- [x] `status-bar.png` - Bottom status bar

---

## 2. Materials Management (`screenshots/materials/`)

### Materials Panel
- [x] `materials-panel-overview.png` - Materials management panel with material list
- [ ] `materials-panel-empty.png` - Empty materials panel (for tutorials)
- [x] `materials-list-cement.png` - List showing cement materials
- [x] `materials-list-aggregates.png` - List showing aggregate materials
- [x] `materials-context-menu.png` - Right-click context menu

### Cement Dialog
- [x] `cement-dialog-properties.png` - Cement properties dialog (Properties tab)
- [x] `cement-dialog-composition.png` - Cement composition tab
- [x] `cement-dialog-psd.png` - Cement PSD tab with curve
- [x] `cement-dialog-advanced.png` - Cement advanced properties tab

### Aggregate Dialogs
- [x] `aggregate-dialog-properties.png` - Aggregate properties
- [x] `aggregate-dialog-grading.png` - Aggregate grading tab
- [x] `fine-aggregate-example.png` - Complete fine aggregate entry
- [x] `coarse-aggregate-example.png` - Complete coarse aggregate entry

### Other Materials
- [x] `limestone-dialog.png` - Limestone filler dialog
- [x] `silica-fume-dialog.png` - Silica fume dialog
- [x] `fly-ash-dialog.png` - Fly ash dialog
- [x] `slag-dialog.png` - Slag dialog

### PSD Curves
- [x] `psd-rosenfeld-example.png` - Example Rosenfeld PSD curve
- [x] `psd-custom-example.png` - Custom PSD data entry

---

## 3. Mix Design (`screenshots/mix-design/`)

### Main Panel
- [x] `mix-design-panel-overview.png` - Mix design panel main view
- [x] `mix-design-panel-empty.png` - Empty mix design (for tutorials)
- [x] `mix-design-loaded.png` - Loaded mix design with all fields filled

### Components
- [x] `mix-design-cement-selection.png` - Cement selection dropdown
- [x] `mix-design-aggregate-selection.png` - Aggregate selection
- [x] `mix-design-scm-selection.png` - SCM (supplementary materials) selection
- [x] `mix-design-system-size.png` - System size and resolution settings

### Grading
- [x] `grading-curve-dialog.png` - Grading curve editor
- [x] `grading-curve-fine-aggregate.png` - Fine aggregate grading curve plot
- [x] `grading-curve-coarse-aggregate.png` - Coarse aggregate grading curve plot
- [x] `grading-template-management.png` - Grading template dialog

### Flocculation
- [x] `flocculation-settings.png` - Flocculation parameter settings
- [x] `particle-shape-selection.png` - Particle shape selector

### Saved Mix Designs
- [x] `saved-mix-designs-list.png` - List of saved mix designs
- [x] `load-mix-design-dialog.png` - Load saved mix design dialog

---

## 4. Microstructure Generation (`screenshots/microstructure/`)

- [ ] `microstructure-panel-overview.png` - Microstructure generation panel
- [ ] `microstructure-parameters.png` - Generation parameters section
- [ ] `microstructure-start-dialog.png` - Start generation confirmation
- [x] `microstructure-progress.png` - Generation in progress
- [x] `microstructure-complete.png` - Generation complete status

---

## 5. Hydration Simulation (`screenshots/hydration/`)

### Main Panel
- [x] `hydration-panel-overview.png` - Hydration panel main view
- [x] `hydration-microstructure-selection.png` - Source microstructure selection

### Curing Conditions
- [x] `hydration-curing-isothermal.png` - Isothermal curing settings
- [x] `hydration-curing-adiabatic.png` - Adiabatic curing settings
- [x] `hydration-temperature-profile.png` - Custom temperature profile

### Advanced Settings
- [x] `hydration-time-calibration.png` - Time conversion factor settings
- [x] `hydration-advanced-params.png` - Advanced hydration parameters
- [x] `hydration-database-mods.png` - Database modification settings

### Execution
- [x] `hydration-start-dialog.png` - Start hydration confirmation
- [x] `hydration-progress.png` - Hydration in progress
- [x] `hydration-complete.png` - Hydration complete status

---

## 6. Elastic Calculations (`screenshots/elastic/`)

### Main Panel
- [x] `elastic-panel-ovexrview.png` - Elastic moduli panel
- [x] `elastic-hydration-selection.png` - Source hydration selection
- [x] `elastic-parameters.png` - Elastic calculation parameters
- [x] `elastic-aggregate-moduli.png` - Aggregate moduli settings

### Execution
- [x] `elastic-start-dialog.png` - Start calculation confirmation
- [x] `elastic-progress.png` - Calculation in progress
- [x] `elastic-complete.png` - Calculation complete

### Results
- [x] `elastic-effective-moduli.png` - Effective moduli viewer dialog
- [x] `elastic-itz-analysis.png` - ITZ analysis viewer dialog
- [x] `elastic-itz-plot.png` - ITZ moduli vs distance plot

---

## 7. Results Visualization (`screenshots/results/`)

### Results Panel
- [x] `results-panel-overview.png` - Results panel with operation list
- [x] `results-panel-buttons.png` - Available analysis buttons

### 3D Microstructure Viewer
- [x] `3d-viewer-microstructure.png` - 3D microstructure visualization
- [x] `3d-viewer-controls.png` - 3D viewer control panel
- [x] `3d-viewer-phase-data.png` - Phase data dialog
- [x] `3d-viewer-connectivity.png` - Connectivity analysis dialog
- [x] `3d-viewer-cross-section.png` - Cross-section view
- [x] `3d-viewer-isometric.png` - Isometric view
- [x] `3d-viewer-orthographic-xy.png` - XY orthographic view

### Hydration Results
- [x] `hydration-results-viewer.png` - Hydration results 3D viewer
- [x] `hydration-time-slider.png` - Time evolution slider
- [x] `hydration-plot-degree.png` - Degree of hydration plot

### Strain Energy Visualization
- [x] `strain-energy-3d-volume.png` - Volume rendering mode
- [x] `strain-energy-3d-isosurface.png` - Isosurface rendering mode
- [x] `strain-energy-3d-pixel.png` - Pixel art rendering mode
- [x] `strain-energy-controls.png` - Strain energy viewer controls
- [x] `strain-energy-cross-section.png` - Cross-section with strain energy
- [x] `strain-energy-threshold-presets.png` - Threshold preset buttons

---

## 8. Operations Monitoring (`screenshots/operations/`)

- [ ] `operations-panel-overview.png` - Operations monitoring panel
- [ ] `operations-panel-multiple.png` - Multiple operations shown
- [ ] `operations-running.png` - Operation in running state
- [ ] `operations-paused.png` - Operation paused
- [ ] `operations-completed.png` - Completed operations
- [ ] `operations-context-menu.png` - Right-click context menu
- [ ] `operations-progress-details.png` - Progress details expanded

---

## Screenshot Guidelines

### Technical Requirements
- **Resolution**: Capture at actual display resolution (not scaled)
- **Format**: PNG (lossless, good for UI)
- **Size**: Try to keep individual screenshots under 2MB
- **Window sizing**: Consistent window sizes when possible

### Content Guidelines
- **Clean data**: Use meaningful example data (not "test123")
- **Readable text**: Ensure all text is crisp and readable
- **Highlight important areas**: Consider adding red boxes/arrows for key features (can be done in post)
- **No personal data**: Avoid showing any sensitive information
- **Professional appearance**: Clean desktop background, hide unnecessary apps

### macOS Screenshot Shortcuts
- `Cmd + Shift + 3`: Capture entire screen
- `Cmd + Shift + 4`: Capture selection (drag to select area)
- `Cmd + Shift + 4, then Space`: Capture specific window (with shadow)
- `Cmd + Shift + 5`: Screenshot utility (more options)

**Pro tip**: Use `Cmd + Shift + 4 + Space` to capture individual windows with nice shadows!

---

## Progress Tracking

Total Screenshots Needed: ~70-80
- [ ] General UI (4)
- [ ] Materials (15)
- [ ] Mix Design (12)
- [ ] Microstructure (5)
- [ ] Hydration (12)
- [ ] Elastic (10)
- [ ] Results (16)
- [ ] Operations (7)

---

## Notes
- Screenshots will be referenced in documentation using relative paths:
  ```markdown
  ![Description](../assets/images/screenshots/category/filename.png)
  ```
- Consider taking extra screenshots for edge cases or errors
- You can always add more screenshots later as documentation develops
