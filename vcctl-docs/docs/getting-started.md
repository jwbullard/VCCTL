# Getting Started with VCCTL

Welcome to VCCTL (Virtual Cement and Concrete Testing Laboratory)! This guide will walk you through creating your first concrete microstructure simulation from start to finish.

## What You'll Learn

In this tutorial, you'll learn how to:

1. Create and manage cement materials
2. Design a concrete mix
3. Generate a 3D microstructure
4. Run a hydration simulation
5. View and analyze results

By the end, you'll have a complete understanding of the basic VCCTL workflow.

## Prerequisites

- VCCTL installed and running on your system
- Basic understanding of concrete materials and hydration
- Approximately 30-60 minutes for your first complete simulation

## Step 1: Launch VCCTL

Start VCCTL from your applications menu or command line. You'll see the main window with several tabs along the upper tab bar:

- **Materials** - Manage cement, aggregates, and supplementary materials
- **Mix Design** - Create concrete mixture designs
- **Microstructure** - Generate 3D particle arrangements
- **Hydration** - Simulate cement hydration over time
- **Elastic Moduli** - Calculate mechanical properties
- **Operations** - Monitor running simulations
- **Results** - View and analyze simulation outputs

## Step 2: Create a Cement Material

Before designing a mix, you need cement. VCCTL comes with a library of pre-defined cements, but let's create a custom one.

### 2.1 Open Materials Panel

Click on the **Materials** panel in the left sidebar.

### 2.2 Create New Cement

1. Click the **"+ New"** button in the Materials toolbar
2. Select **"Cement"** from the material type dropdown
3. Enter a name like **"MyFirstCement"**

### 2.3 Define Cement Properties

Fill in the basic properties:

- **Bulk Density**: 3150 kg/m³ (typical for Portland cement)
- **Specific Gravity**: 3.15
- **Blaine Fineness**: 380 m²/kg (typical for Type I/II cement)

### 2.4 Set Phase Composition

Switch to the **Composition** tab and enter the Bogue phase composition (percentages should sum to 100):

- **C3S (Alite)**: 55%
- **C2S (Belite)**: 18%
- **C3A (Aluminate)**: 10%
- **C4AF (Ferrite)**: 8%
- **Gypsum**: 5%
- **Inert**: 4%

### 2.5 Configure Particle Size Distribution

Switch to the **PSD** tab:

1. Select **"Rosin-Rammler"** distribution type
2. Set **Minimum Size**: 0.5 μm
3. Set **Maximum Size**: 50.0 μm
4. Set **Characteristic Size**: 15.0 μm
5. Set **Spread Parameter**: 1.0

Click **"Save"** to store your cement material.

## Step 3: Design Your Mix

Now that you have cement, let's create a mortar using that cement.

### 3.1 Open Mix Design Panel

Click on the **Mix Design** tab in the upper tab bar.

### 3.2 Create New Mix

1. Enter a mix name like **"MyFirstMix"** in the Mix Design Name field
2. The mix will auto-save as you work

### 3.3 Add Cement to Mix

In the **Powder Components** section:

1. Click **"+ Add Component"**
2. Select **"MyFirstCement"** from the cement dropdown
3. Set **Mass**: 1000 kg

### 3.4 Add Water

1. In the **Water Content** section, set **w/b**: 0.4
2. The water mass will be calculated and updated automatically to 400 kg

### 3.5 Add Fine Aggregate

1. In the **Mortar/Concrete Options** section, set **Fine Aggregate Mass**: 1380
   kg
2. From the **Fine Aggregate** dropdown menu, select **MA106A-1-fine**, which is
   the ASTM standard sand.
3. Click the **Grading...** button.
4. In the grading dialog window, select **ASTM-C109** from the template dropdown
   menu.
5. Click the **Apply** button in the lower right corner of the dialog window.

### 3.6 Configure System Parameters

In the **System Settings** section:

- **System Size X**: 100 voxels
- **System Size Y**: 100 voxels
- **System Size Z**: 100 voxels
- **Resolution**: 1.0 μm/voxel

This creates a 100 × 100 × 100 μm³ microstructure.

### 3.7 Review Mix Summary

Check the **Mix Summary** panel to verify:

- Total mass
- Volume fractions
- Water-cement ratio

### 3.8 Validate Mix (Optional)

1. Scroll to the bottom of the page.
2. Click the **Validate** button in the lower right corner
3. A message will appear in the **Validation Results°° section that gives
   information about the designed mixture. The message is only general
engineering information and will not affect the application in any way.

### Step 3.9: Generate Microstructure

Click the **Create Mix** button on the lower right corner of the window to begin
creating a 3D instance of the binder microstructure based on your mixture
design.

### 3.10 Monitor Progress

Switch to the **Operations** tab to watch progress. In the displayed list of operations, click on the operation corresponding to your mixture design.

You'll see status updates like:
- "Placing cement particles..."
- "Distributing clinker phases..."
- "Writing output file..."

Generation of a 3D microstructure typically takes 5-30 minutes depending on system size, w/b ratio, and choice of particle shapes.

## Step 4: Run Hydration Simulation

Once microstructure generation completes, simulate cement hydration.

### 4.1 Open Hydration Panel

Click on the **Hydration** tab in the left sidebar.

### 4.2 Select Source Microstructure

1. Enter an operation name like **"HydrationOf-MyFirstMicrostructure"**
2. Click **"Select Microstructure"** button
3. Choose **"MyFirstMicrostructure"** from the list
4. All microstructure parameters will populate automatically

### 4.3 Configure Hydration Settings

In the **Time & Cycles** section:

- **Max DOH**: 1.0 (no limit on hydration)
- **Max Time**: 168 hours (7 days of hydration)

In the **Time Calibration Mode** section:

- **Time Calibration Mode**: Knudsen parabolic
- **Time Conversion Factor**: 0.00035
- **Temperature**: 25°C (room temperature curing)

### 4.4 Set Curing Conditions

In the **Curing Conditions** section:

- **Thermal Conditions**: Isothermal (constant temperature)
- **Moisture Conditions**: Sealed (no water replenishment)

### 4.5 Start Simulation

1. Click **"Start Simulation"**
2. The operation will appear in the **Operations** panel

### 4.6 Monitor Progress

Switch to the **Operations** panel to watch progress. Hydration simulations typically take 30-90 minutes depending on system size and simulation time.

You'll see status updates showing:
- Current simulation time
- Percent complete
- Degree of hydration

## Step 5: View Results

After hydration completes, analyze your results.

### 5.1 Open Results Panel

Click on the **Results** tab in the upper tab bar.

### 5.2 Select Your Operation

Click on **"HydrationOf-MyFirstMicrostructure"** in the operations list.

### 5.3 View 3D Microstructure

1. Click **"View 3D Results"** button
2. A 3D visualization window will open showing your hydrated microstructure
3. Use the **Isometric** button to see an isometric view
4. Use the **XY**, **XZ**, or **YZ** buttons to see orthographic projections.
3. Use the arrow buttons to rotate the view
4. Use the **Zoom+** and **Zoom-** buttons to zoom in/out
5. Use the **Cross-Sections** buttons and sliders to slice the view and see the interior

### 6.4 Explore Phase Data

In the 3D viewer:

1. Enable **"Phase Data"** checkbox to see phase information
2. Toggle individual phases on/off to examine specific materials

### 6.5 View 2D Data Plots

1. Click **"Plot Data"** button in the Results panel
2. View graphs of:
   - Degree of hydration vs. time
   - Phase volumes vs. time
   - Temperature profiles (if adiabatic curing)
3. Plot multiple properties on the same line using a common abcissa such as
   time

## Next Steps

Congratulations! You've completed your first VCCTL simulation. Here are some ways to expand your knowledge:

### Learn More About Each Component

- **[Materials Management](user-guide/materials-management.md)** - Deep dive into material properties and PSD definitions
- **[Mix Design](user-guide/mix-design.md)** - Advanced mixing strategies and optimization
- **[Microstructure Generation](user-guide/microstructure-generation.md)** - Particle placement algorithms and flocculation
- **[Hydration Simulation](user-guide/hydration-simulation.md)** - Advanced curing conditions and temperature effects
- **[Results Visualization](user-guide/results-visualization.md)** - Advanced analysis and data export

### Try Advanced Workflows

- **[Parameter Studies](workflows/parameter-studies.md)** - Systematically explore w/c ratio, temperature, etc.
- **[Multi-Material Mixes](workflows/advanced-analysis.md)** - Add fly ash, slag, or other supplementary materials
- **[Elastic Moduli Calculations](user-guide/elastic-calculations.md)** - Compute mechanical properties from hydrated microstructures

### Troubleshooting

If you encounter issues, check the **[Troubleshooting Guide](troubleshooting.md)** for solutions to common problems.

## Tips for Success

1. **Start Small**: Use smaller system sizes (50-100 voxels) for initial testing to get faster results
2. **Save Often**: VCCTL auto-saves mix designs, but operations can be renamed/deleted if needed
3. **Monitor Memory**: Large systems (200+ voxels) can require significant RAM
4. **Use Defaults**: The default parameters are carefully chosen for typical simulations
5. **Check Units**: Pay attention to units (μm, hours, kg/m³) to avoid mistakes

## Summary

You've learned the complete VCCTL workflow:

1. ✅ Created a cement material with composition and PSD
2. ✅ Designed a concrete mix with water-cement ratio
3. ✅ Generated a 3D microstructure
4. ✅ Ran a hydration simulation
5. ✅ Visualized and analyzed results

This foundation will serve you well as you explore VCCTL's advanced capabilities for concrete modeling and analysis.

---

**Ready to dive deeper?** Continue with the [Materials Management](user-guide/materials-management.md) guide to learn about all six material types and advanced PSD configurations.
