#!/usr/bin/env python3
"""
Help Manager

Manages help content, topics, and provides centralized access to documentation.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class HelpTopic:
    """Represents a single help topic."""
    
    def __init__(self, topic_id: str, title: str, content: str, 
                 keywords: List[str] = None, parent_section: str = None):
        self.topic_id = topic_id
        self.title = title
        self.content = content
        self.keywords = keywords or []
        self.parent_section = parent_section
        self.related_topics = []
        self.screenshots = []


class HelpSection:
    """Represents a section containing multiple help topics."""
    
    def __init__(self, section_id: str, title: str, description: str = "", 
                 icon_name: str = "help-contents"):
        self.section_id = section_id
        self.title = title
        self.description = description
        self.icon_name = icon_name
        self.topics = {}
        self.subsections = {}
    
    def add_topic(self, topic: HelpTopic):
        """Add a topic to this section."""
        topic.parent_section = self.section_id
        self.topics[topic.topic_id] = topic
    
    def add_subsection(self, subsection: 'HelpSection'):
        """Add a subsection to this section."""
        self.subsections[subsection.section_id] = subsection


class HelpManager(GObject.Object):
    """
    Central manager for help system.
    
    Features:
    - Hierarchical help content organization
    - Search functionality
    - Context-sensitive help
    - Bookmark management
    - History tracking
    """
    
    __gsignals__ = {
        'help-requested': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'topic-viewed': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }
    
    def __init__(self):
        super().__init__()
        self.sections = {}
        self.topics_index = {}
        self.search_index = {}
        self.bookmarks = []
        self.history = []
        self.current_topic = None
        
        self._initialize_help_content()
    
    def _initialize_help_content(self):
        """Initialize default help content."""
        self._create_getting_started_section()
        self._create_materials_section()
        self._create_mix_design_section()
        self._create_simulation_section()
        self._create_troubleshooting_section()
        
        self._build_search_index()
    
    def _create_getting_started_section(self):
        """Create getting started help section."""
        section = HelpSection(
            "getting_started",
            "Getting Started",
            "Learn the basics of using VCCTL",
            "system-run"
        )
        
        # Overview topic
        overview_topic = HelpTopic(
            "overview",
            "VCCTL Overview",
            """
# VCCTL Overview

VCCTL (Virtual Cement and Concrete Testing Laboratory) is a comprehensive simulation software for cement and concrete materials.

## Key Features

- **Material Definition**: Create and manage cement, aggregate, and supplementary materials
- **Mix Design**: Design concrete mixes with automated calculations
- **Microstructure Generation**: Generate realistic 3D microstructures
- **Hydration Simulation**: Simulate cement hydration processes
- **Property Prediction**: Predict mechanical and transport properties

## Workflow

The typical VCCTL workflow follows these steps:

1. **Define Materials**: Create cement, aggregates, and other materials
2. **Design Mix**: Specify proportions and create mix design
3. **Generate Microstructure**: Create 3D representation of concrete
4. **Run Simulation**: Execute hydration and property calculations
5. **Analyze Results**: Review predictions and export data

## Getting Help

- Use **F1** to open this help system
- Hover over controls for contextual tooltips
- Check the status bar for additional information
- Visit the troubleshooting section for common issues
            """,
            ["overview", "introduction", "basics", "workflow"]
        )
        section.add_topic(overview_topic)
        
        # Interface topic
        interface_topic = HelpTopic(
            "interface",
            "User Interface",
            """
# User Interface

The VCCTL interface is organized into several main areas:

## Menu Bar

- **File**: New, open, save, export operations
- **Edit**: Undo, redo, copy, paste operations  
- **View**: Display options and panel management
- **Tools**: Utilities and preferences
- **Help**: Documentation and about information

## Toolbar

Quick access to common operations:
- New project
- Open/Save project
- Material creation tools
- Simulation controls

## Main Panel

The central workspace containing:
- **Materials Panel**: Manage cement, aggregates, admixtures
- **Mix Design Panel**: Create and edit concrete mix designs
- **Simulation Panel**: Configure and run simulations
- **Results Panel**: View and analyze simulation outputs

## Properties Panel

Detailed property editor for selected materials or mix designs.

## Status Bar

Displays current operation status, progress indicators, and help text.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New project |
| Ctrl+O | Open project |
| Ctrl+S | Save project |
| F1 | Open help |
| F5 | Refresh |
            """,
            ["interface", "ui", "toolbar", "panels", "shortcuts"]
        )
        section.add_topic(interface_topic)
        
        self.add_section(section)
    
    def _create_materials_section(self):
        """Create materials help section."""
        section = HelpSection(
            "materials",
            "Materials",
            "Working with cement, aggregates, and other materials",
            "applications-science"
        )
        
        # Cement materials topic
        cement_topic = HelpTopic(
            "cement_materials",
            "Cement Materials",
            """
# Cement Materials

Cement is the primary binding agent in concrete. VCCTL supports various cement types with detailed chemical compositions.

## Creating Cement Materials

1. Click **New Cement** in the Materials panel
2. Enter basic properties:
   - Name (descriptive identifier)
   - Type (I, II, III, IV, V)
   - Density (typically 3.15 g/cm³)

3. Specify chemical composition:
   - SiO₂ (Silicon dioxide): 18-25%
   - Al₂O₃ (Aluminum oxide): 3-8%
   - Fe₂O₃ (Iron oxide): 1-5%
   - CaO (Calcium oxide): 60-67%
   - MgO (Magnesium oxide): 0.5-4%
   - SO₃ (Sulfur trioxide): 1-4%

4. Add physical properties:
   - Blaine fineness (cm²/g)
   - Particle size distribution

## Validation

VCCTL validates cement compositions:
- Total oxides should sum to ~100%
- Individual oxides within realistic ranges
- Chemical compatibility checks

## Tips

- Use standard ASTM cement types as starting points
- Ensure accurate chemical analysis data
- Consider fineness impact on hydration rate
            """,
            ["cement", "materials", "composition", "oxides", "astm"]
        )
        section.add_topic(cement_topic)
        
        # Aggregate materials topic
        aggregate_topic = HelpTopic(
            "aggregate_materials", 
            "Aggregate Materials",
            """
# Aggregate Materials

Aggregates form the skeleton of concrete and significantly affect properties.

## Types of Aggregates

### Fine Aggregates (Sand)
- Particle size: passing 4.75 mm sieve
- Fineness modulus: 2.3 - 3.1
- Common sources: river sand, manufactured sand

### Coarse Aggregates (Gravel/Stone)
- Particle size: retained on 4.75 mm sieve
- Maximum size: typically 19 mm or 25 mm
- Common sources: crushed stone, gravel

## Properties to Define

### Basic Properties
- Density (bulk and apparent)
- Absorption capacity
- Moisture content

### Gradation
- Sieve analysis results
- Fineness modulus (fine aggregates)
- Maximum aggregate size

### Advanced Properties
- Shape factors (elongation, flakiness)
- Surface texture
- Mineralogy

## Creating Aggregates

1. Select aggregate type (fine/coarse)
2. Enter physical properties
3. Input gradation data from sieve analysis
4. Specify additional properties as needed

## Quality Considerations

- Well-graded aggregates improve workability
- Angular particles increase strength
- Absorption affects mix water requirements
- Alkali-reactive aggregates require special consideration
            """,
            ["aggregate", "sand", "gravel", "gradation", "density"]
        )
        section.add_topic(aggregate_topic)
        
        self.add_section(section)
    
    def _create_mix_design_section(self):
        """Create mix design help section."""
        section = HelpSection(
            "mix_design",
            "Mix Design", 
            "Creating and optimizing concrete mix designs",
            "applications-engineering"
        )
        
        mix_design_topic = HelpTopic(
            "concrete_mix_design",
            "Concrete Mix Design",
            """
# Concrete Mix Design

Mix design determines the proportions of materials to achieve desired concrete properties.

## Design Process

### 1. Specify Requirements
- Compressive strength target
- Workability (slump)
- Durability requirements
- Exposure conditions

### 2. Select Materials
- Cement type and source
- Fine and coarse aggregates
- Supplementary cementitious materials
- Chemical admixtures

### 3. Determine Proportions

#### Water-Cement Ratio
- Primary factor for strength and durability
- Lower W/C ratio → higher strength
- Typical range: 0.35 - 0.65

#### Aggregate Proportions
- Coarse aggregate: 60-70% of total aggregate
- Fine aggregate: 30-40% of total aggregate
- Optimize for workability and economics

### 4. Calculate Quantities

For 1 m³ of concrete:
- Cement content (kg/m³)
- Water content (kg/m³)  
- Fine aggregate (kg/m³)
- Coarse aggregate (kg/m³)

## Design Methods

VCCTL supports multiple design approaches:
- ACI 211 method
- DOE method
- Density method
- Custom proportioning

## Trial Mixes

1. Calculate initial proportions
2. Prepare trial batch
3. Test properties (slump, density)
4. Adjust proportions as needed
5. Confirm with additional trials

## Optimization

Use VCCTL's optimization tools to:
- Minimize cement content
- Achieve target strength
- Optimize workability
- Balance cost and performance
            """,
            ["mix design", "proportions", "strength", "workability", "aci"]
        )
        section.add_topic(mix_design_topic)
        
        self.add_section(section)
    
    def _create_simulation_section(self):
        """Create simulation help section."""
        section = HelpSection(
            "simulation",
            "Simulation",
            "Running hydration and property prediction simulations", 
            "applications-simulation"
        )
        
        hydration_topic = HelpTopic(
            "hydration_simulation",
            "Hydration Simulation",
            """
# Hydration Simulation

VCCTL simulates the cement hydration process to predict concrete properties over time.

## Simulation Setup

### 1. Microstructure Generation
- Define system size (100x100x100 μm typical)
- Set particle size distributions
- Generate initial microstructure

### 2. Simulation Parameters
- **Temperature**: Affects hydration rate (typically 20°C)
- **Relative Humidity**: Controls moisture availability
- **Simulation Time**: Duration to simulate (28 days typical)
- **Time Steps**: Resolution of simulation

### 3. Boundary Conditions
- Sealed vs. drying conditions
- Temperature cycling
- Moisture exchange

## Hydration Process

The simulation models:
- Dissolution of cement phases (C₃S, C₂S, C₃A, C₄AF)
- Formation of hydration products (C-S-H, CH, ettringite)
- Microstructure development
- Pore structure evolution

## Output Properties

### Mechanical Properties
- Compressive strength development
- Elastic modulus
- Tensile strength

### Transport Properties  
- Permeability
- Diffusivity
- Sorptivity

### Microstructural Properties
- Degree of hydration
- Porosity
- Phase assemblage

## Running Simulations

1. Verify material definitions
2. Generate microstructure
3. Set simulation parameters
4. Start simulation
5. Monitor progress
6. Analyze results

## Performance Considerations

- Larger systems require more memory
- Longer simulations take more time
- Parallel processing improves speed
- Save intermediate results for analysis
            """,
            ["hydration", "simulation", "microstructure", "properties"]
        )
        section.add_topic(hydration_topic)
        
        self.add_section(section)
    
    def _create_troubleshooting_section(self):
        """Create troubleshooting help section."""
        section = HelpSection(
            "troubleshooting",
            "Troubleshooting",
            "Common issues and solutions",
            "dialog-warning"
        )
        
        common_issues_topic = HelpTopic(
            "common_issues",
            "Common Issues",
            """
# Common Issues and Solutions

## Material Definition Issues

### Invalid Cement Composition
**Problem**: Error message "Cement composition does not sum to 100%"
**Solution**: 
- Check that all oxide percentages sum to ~100% (±2%)
- Verify decimal points are correct
- Include all major oxides (SiO₂, Al₂O₃, Fe₂O₃, CaO, MgO, SO₃)

### Unrealistic Property Values
**Problem**: Warning about unrealistic material properties
**Solution**:
- Verify density values (cement: ~3.15 g/cm³, aggregates: 2.6-2.8 g/cm³)
- Check gradation percentages (should be cumulative passing)
- Ensure fineness values are reasonable

## Mix Design Issues

### High Water Requirement
**Problem**: Mix requires excessive water content
**Solution**:
- Reduce aggregate absorption if overestimated
- Check aggregate gradation for proper packing
- Consider using water reducer admixtures
- Verify slump target is reasonable

### Unbalanced Proportions
**Problem**: Mix proportions seem unrealistic
**Solution**:
- Verify material densities are correct
- Check calculation method selection
- Ensure target properties are achievable
- Review aggregate-to-cement ratio

## Simulation Issues

### Memory Errors
**Problem**: "Out of memory" during microstructure generation
**Solution**:
- Reduce system size (e.g., 50x50x50 instead of 100x100x100)
- Close other applications to free memory
- Use 64-bit version for large simulations
- Consider running on high-memory system

### Slow Simulation
**Problem**: Simulation takes very long time
**Solution**:
- Reduce simulation time or increase time steps
- Use smaller system size for testing
- Enable parallel processing if available
- Check CPU and memory usage

### Convergence Issues
**Problem**: Simulation fails to converge
**Solution**:
- Check material definitions for consistency
- Verify boundary conditions are realistic
- Reduce time step size
- Check for numerical instabilities

## File and Data Issues

### Import Errors
**Problem**: Cannot import material data files
**Solution**:
- Verify file format (JSON, CSV, XML)
- Check file encoding (UTF-8 recommended)
- Validate data completeness
- Ensure proper file permissions

### Export Problems
**Problem**: Results export fails
**Solution**:
- Check available disk space
- Verify write permissions to output directory
- Ensure proper file format selection
- Close files that may be open in other applications

## General Issues

### UI Responsiveness
**Problem**: Interface becomes slow or unresponsive
**Solution**:
- Close unused panels or dialogs
- Reduce data display density
- Update graphics drivers
- Restart application if needed

### Licensing Issues
**Problem**: License validation errors
**Solution**:
- Check network connectivity
- Verify license file location
- Contact support for license renewal
- Ensure system clock is correct

## Getting Additional Help

If problems persist:
1. Check the error log for detailed messages
2. Document steps to reproduce the issue
3. Note system specifications and data used
4. Contact technical support with details
            """,
            ["troubleshooting", "errors", "issues", "solutions", "problems"]
        )
        section.add_topic(common_issues_topic)
        
        self.add_section(section)
    
    def add_section(self, section: HelpSection):
        """Add a help section."""
        self.sections[section.section_id] = section
        
        # Index all topics in the section
        for topic in section.topics.values():
            self.topics_index[topic.topic_id] = topic
    
    def get_section(self, section_id: str) -> Optional[HelpSection]:
        """Get a help section by ID."""
        return self.sections.get(section_id)
    
    def get_topic(self, topic_id: str) -> Optional[HelpTopic]:
        """Get a help topic by ID."""
        return self.topics_index.get(topic_id)
    
    def search_topics(self, query: str) -> List[HelpTopic]:
        """Search help topics by query."""
        query_lower = query.lower()
        matching_topics = []
        
        for topic in self.topics_index.values():
            # Search in title
            if query_lower in topic.title.lower():
                matching_topics.append(topic)
                continue
            
            # Search in content
            if query_lower in topic.content.lower():
                matching_topics.append(topic)
                continue
            
            # Search in keywords
            for keyword in topic.keywords:
                if query_lower in keyword.lower():
                    matching_topics.append(topic)
                    break
        
        return matching_topics
    
    def get_contextual_help(self, context: str) -> Optional[HelpTopic]:
        """Get contextual help for a specific UI context."""
        context_mappings = {
            'materials_panel': 'cement_materials',
            'cement_editor': 'cement_materials',
            'aggregate_editor': 'aggregate_materials',
            'mix_design_panel': 'concrete_mix_design',
            'simulation_panel': 'hydration_simulation',
            'error_dialog': 'common_issues'
        }
        
        topic_id = context_mappings.get(context)
        return self.get_topic(topic_id) if topic_id else None
    
    def add_bookmark(self, topic_id: str):
        """Add a topic to bookmarks."""
        if topic_id not in self.bookmarks:
            self.bookmarks.append(topic_id)
    
    def remove_bookmark(self, topic_id: str):
        """Remove a topic from bookmarks."""
        if topic_id in self.bookmarks:
            self.bookmarks.remove(topic_id)
    
    def add_to_history(self, topic_id: str):
        """Add a topic to view history."""
        if topic_id in self.history:
            self.history.remove(topic_id)
        self.history.insert(0, topic_id)
        
        # Limit history size
        if len(self.history) > 50:
            self.history = self.history[:50]
    
    def get_recent_topics(self, count: int = 10) -> List[HelpTopic]:
        """Get recently viewed topics."""
        recent_topics = []
        for topic_id in self.history[:count]:
            topic = self.get_topic(topic_id)
            if topic:
                recent_topics.append(topic)
        return recent_topics
    
    def show_help(self, topic_id: str = None, context: str = None):
        """Show help dialog with specific topic or context."""
        if context and not topic_id:
            contextual_topic = self.get_contextual_help(context)
            if contextual_topic:
                topic_id = contextual_topic.topic_id
        
        if not topic_id:
            topic_id = "overview"  # Default to overview
        
        self.emit('help-requested', topic_id)
    
    def _build_search_index(self):
        """Build search index for fast topic lookup."""
        for topic in self.topics_index.values():
            words = (topic.title + " " + topic.content + " " + " ".join(topic.keywords)).lower().split()
            for word in words:
                if word not in self.search_index:
                    self.search_index[word] = []
                if topic not in self.search_index[word]:
                    self.search_index[word].append(topic)