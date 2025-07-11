# VCCTL GTK3 Desktop Application

Virtual Cement and Concrete Testing Laboratory (VCCTL) - Native Desktop Application

## Overview

This is the GTK3/Python desktop version of the VCCTL (Virtual Cement and Concrete Testing Laboratory) developed by NIST's Building and Fire Research Laboratory. The application provides a comprehensive virtual laboratory for modeling and simulating cement and concrete materials.

## Features

- **Materials Management**: Cement compositions, fly ash, slag, aggregates, and inert fillers
- **Mix Design**: Virtual concrete/mortar mixture creation and validation
- **Microstructure Generation**: 3D virtual material structures
- **Simulation Control**: Hydration modeling and property prediction
- **Data Visualization**: Real-time plots and analysis
- **File Operations**: Import/export materials and simulation data

## Requirements

### System Requirements
- **Operating System**: Linux (primary), Windows 10+, macOS 10.14+
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

Coming soon: AppImage (Linux), Windows installer, and macOS app bundle.

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

## Development

### Running Tests
```bash
pytest src/tests/
```

### Code Formatting
```bash
black src/
```

### Type Checking
```bash
mypy src/
```

### Linting
```bash
flake8 src/
```

## Contributing

This project follows NIST software development guidelines. Please ensure all code:
- Follows PEP 8 style guidelines
- Includes appropriate type hints
- Has comprehensive test coverage
- Is properly documented

## License

This software was developed by NIST employees and is not subject to copyright protection in the United States. This software may be subject to foreign copyright. The identification of certain commercial equipment, instruments, or materials does not imply recommendation or endorsement by NIST, nor does it imply that the materials or equipment identified are necessarily the best available for the purpose.

## Contact

For questions or support, please contact the VCCTL development team at:
- Email: vcctl@nist.gov
- Website: https://vcctl.nist.gov/

## Acknowledgments

This desktop application is a conversion of the original VCCTL web application developed by NIST's Building and Fire Research Laboratory. The conversion maintains all functionality while providing a native desktop experience using GTK3 and Python.