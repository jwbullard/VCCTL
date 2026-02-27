# VCCTL GTK3 Desktop Application

Virtual Cement and Concrete Testing Laboratory (VCCTL) - Native Desktop Application

## Overview

This is the GTK3/Python desktop version of the VCCTL (Virtual Cement and Concrete Testing Laboratory) originally developed at NIST's Building and Fire Research Laboratory. The application provides a virtual laboratory for modeling and simulating cement and concrete materials.

## Features

- **Materials Management**: Cement compositions, fly ash, slag, aggregates, and inert fillers
- **Mix Design**: Virtual concrete/mortar mixture creation and validation
- **Microstructure Generation**: 3D virtual material structures
- **Simulation Control**: Hydration modeling and property prediction
- **Data Visualization**: Real-time plots and analysis
- **File Operations**: Import/export materials and simulation data

## Requirements

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+
- **Python**: 3.8+ (recommended 3.11+)
- **GTK3**: 3.24+
- **Memory**: 512MB RAM minimum, 1GB recommended
- **Storage**: 100MB application + database storage

### Python Dependencies
See `requirements.txt` for complete list of dependencies.

## Installation

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd vcctl-gtk
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv vcctl-gtk-env
   source vcctl-gtk-env/bin/activate  # On Linux/macOS
   # or
   vcctl-gtk-env\Scripts\activate     # On Windows
   ```

3. **Install system dependencies** (Ubuntu/Debian):
   ```bash
   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
   sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config
   ```

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```bash
   python src/main.py
   ```

### Production Installation

Windows installer, and macOS app bundle.

## Project Structure

```
vcctl-gtk/
├── src/
│   ├── main.py                 # Application entry point
│   ├── app/
│   │   ├── application.py      # Main GTK Application class
│   │   ├── windows/            # UI windows and dialogs
│   │   ├── models/             # Data models (SQLAlchemy)
│   │   ├── services/           # Business logic layer
│   │   ├── database/           # Database management
│   │   ├── utils/              # Utility functions
│   │   └── resources/          # Images, CSS, UI files
│   ├── tests/                  # Test suite
│   └── data/                   # Database and material data
├── requirements.txt            # Python dependencies
├── setup.py                   # Package configuration
└── README.md                  # This file
```

## Contributing

Contact the development team with suggestions for new or better features, including
code to implement those features. The development team can be contacted at
[jwbullard@tamu.edu](mailto:jwbullard@tamu.edu)

## License

Copyright (c) 2020-present Jeffrey W. Bullard

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the “Software”), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom
the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Contact

For questions or support, please contact the VCCTL development team at
[jwbullard@tamu.edu](mailto:jwbullard@tamu.edu)

## Acknowledgments

This desktop application is a conversion and augmentation of the original VCCTL web application originally developed by NIST's Building and Fire Research Laboratory. The conversion maintains much of the original functionality while adding new features and providing a native desktop experience using GTK3 and Python. VCCTL's principal developers are Dale P. Bentz (NIST, retired), Edward J. Garboczi (NIST, retired), and Jeffrey W. Bullard (formerly NIST, currently Texas A&M University).
