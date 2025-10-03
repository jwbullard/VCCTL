# VCCTL - Virtual Cement and Concrete Testing Laboratory

## Welcome to VCCTL

**Version 10.0.0**

VCCTL is an integrated software package for simulating the 3D microstructure generation, hydration, and mechanical properties of cementitious materials. Developed at Texas A&M University and based on work originating at the National Institute of Standards and Technology (NIST), VCCTL provides researchers and engineers with powerful tools for understanding and predicting the behavior of concrete and other cementitious systems.

---

## Key Features

### 🏗️ **Comprehensive Materials Database**
- Manage cement, aggregate, supplementary cementitious materials, and admixtures
- Built-in particle size distribution (PSD) support
- Import and export material data

### 📊 **Advanced Mix Design**
- Interactive mix design interface with auto-save functionality
- Grading curve visualization and management
- Aggregate packing optimization
- Flocculation modeling

### 🔬 **3D Microstructure Generation**
- Generate realistic 3D digital microstructures using the genmic algorithm
- Customizable system size and resolution
- Real-time progress monitoring
- Support for complex multi-phase systems

### ⚗️ **Hydration Simulation**
- Time-dependent hydration kinetics modeling
- Thermal effects and curing condition simulation
- Advanced parameter calibration
- Temperature profile support

### 🔧 **Mechanical Property Prediction**
- Elastic moduli calculations
- Strain energy visualization with PyVista
- Interfacial Transition Zone (ITZ) analysis
- Directional property evaluation

### 📈 **Results Visualization**
- Interactive 3D microstructure visualization
- Phase connectivity and percolation analysis
- Cross-sectional analysis
- Professional plotting and data export

---

## Quick Start

New to VCCTL? Get started with these essential resources:

1. **[Installation Guide](installation.md)** - Install VCCTL on your platform
2. **[Getting Started](getting-started.md)** - Your first concrete simulation in 30 minutes
3. **[User Guide](user-guide/materials-management.md)** - Comprehensive feature documentation
4. **[Workflows](workflows/basic-concrete-simulation.md)** - End-to-end tutorial examples

---

## What's New in Version 10.0

!!! success "Major Updates"
    - **Complete GTK3 User Interface** - Modern, responsive desktop application
    - **Enhanced 3D Visualization** - PyVista integration for professional rendering
    - **Strain Energy Analysis** - Advanced elastic property visualization
    - **ITZ Analysis** - Detailed interfacial transition zone characterization
    - **Python-Based Connectivity** - Memory-efficient percolation analysis
    - **Improved Progress Monitoring** - Real-time operation tracking with pause/resume

---

## System Requirements

=== "Minimum"
    - **OS**: macOS 11+, Windows 10+, or Linux (Ubuntu 20.04+)
    - **RAM**: 8 GB
    - **Storage**: 2 GB free space
    - **Display**: 1280x800 resolution

=== "Recommended"
    - **OS**: macOS 14+, Windows 11+, or Linux (Ubuntu 22.04+)
    - **RAM**: 16 GB or more
    - **Storage**: 10 GB+ free space for simulations
    - **Display**: 1920x1080 resolution or higher
    - **GPU**: Optional - for enhanced 3D visualization

---

## Community & Support

- **GitHub**: [jwbullard/VCCTL](https://github.com/jwbullard/VCCTL)
- **Issues**: Report bugs and request features on GitHub
- **Documentation**: This site is regularly updated with new content

---

## Citation

If you use VCCTL in your research, please cite:

```bibtex
@software{vcctl2025,
  title = {VCCTL: Virtual Cement and Concrete Testing Laboratory},
  author = {Bullard, Jeffrey W.},
  year = {2025},
  version = {10.0.0},
  organization = {Texas A\&M University},
  url = {https://github.com/jwbullard/VCCTL}
}
```

---

## License

VCCTL is released under the MIT License.

!!! info "MIT License"
    Copyright (c) 2020-present Jeffrey W. Bullard

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Acknowledgments

VCCTL originated at the National Institute of Standards and Technology with the work of Dale P. Bentz and Edward J. Garboczi and over the past 20 years has benefited from meaningful contributions by Jeffrey W. Bullard, Nicos S. Martys, and Kenneth A. Snyder.
