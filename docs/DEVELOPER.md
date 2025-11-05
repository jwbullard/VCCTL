# VCCTL Developer Documentation

**Virtual Cement and Concrete Testing Laboratory**  
**Desktop Application Developer Guide**

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Environment](#development-environment)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [UI Framework](#ui-framework)
6. [Data Models](#data-models)
7. [Service Layer](#service-layer)
8. [Database Integration](#database-integration)
9. [Testing Framework](#testing-framework)
10. [Build and Deployment](#build-and-deployment)
11. [Contributing Guidelines](#contributing-guidelines)
12. [API Reference](#api-reference)

---

## Architecture Overview

VCCTL desktop application follows a layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│                UI Layer                 │
│  (GTK3 Windows, Panels, Dialogs)      │
├─────────────────────────────────────────┤
│              Service Layer              │
│  (Business Logic, Operations)          │
├─────────────────────────────────────────┤
│              Data Layer                 │
│  (Models, Repositories, Database)      │
├─────────────────────────────────────────┤
│              Utility Layer              │
│  (File I/O, Error Handling, Utils)    │
└─────────────────────────────────────────┘
```

### Key Design Principles

- **Separation of Concerns**: Clear boundaries between UI, business logic, and data
- **Dependency Injection**: Service container manages dependencies
- **Event-Driven Architecture**: GObject signals for loose coupling
- **Error Handling**: Centralized error management and user feedback
- **Performance Monitoring**: Built-in performance tracking and optimization
- **Accessibility**: WCAG 2.1 compliant UI with screen reader support
- **Testability**: Comprehensive unit, integration, and end-to-end testing

### Technology Stack

- **Language**: Python 3.8+
- **UI Framework**: GTK3 via PyGObject
- **Database**: SQLite with SQLAlchemy ORM
- **Data Validation**: Pydantic models
- **Testing**: pytest with comprehensive coverage
- **Documentation**: Sphinx with reStructuredText
- **Code Quality**: Black, flake8, mypy

---

## Development Environment

### Prerequisites

- Python 3.8 or higher
- GTK3 development libraries
- Git version control
- Text editor or IDE (VS Code, PyCharm recommended)

### Setup Instructions

1. **Clone Repository**
   ```bash
   git clone https://github.com/usnistgov/vcctl.git
   cd vcctl/desktop
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv dev-env
   source dev-env/bin/activate  # Linux/macOS
   # or
   dev-env\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

4. **Setup Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Run Initial Tests**
   ```bash
   pytest tests/
   ```

### Development Tools

#### Code Formatting
```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/
```

#### Linting
```bash
# Check code quality
flake8 src/ tests/

# Type checking
mypy src/
```

#### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e
```

---

## Project Structure

```
vcctl-gtk/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── application.py          # Main application class
│       ├── database/               # Database layer
│       │   ├── __init__.py
│       │   ├── service.py          # Database service
│       │   ├── models.py           # SQLAlchemy models
│       │   └── migrations/         # Database migrations
│       ├── help/                   # Help system
│       │   ├── __init__.py
│       │   ├── help_manager.py     # Help content management
│       │   ├── help_dialog.py      # Help dialog UI
│       │   └── tooltip_manager.py  # Tooltip system
│       ├── models/                 # Data models
│       │   ├── __init__.py
│       │   ├── cement.py           # Cement material models
│       │   ├── aggregate.py        # Aggregate material models
│       │   └── mix_design.py       # Mix design models
│       ├── services/               # Business logic layer
│       │   ├── __init__.py
│       │   ├── service_container.py # Dependency injection
│       │   ├── cement_service.py   # Cement operations
│       │   ├── aggregate_service.py # Aggregate operations
│       │   └── file_operations_service.py # File I/O
│       ├── ui/                     # UI polish system
│       │   ├── __init__.py
│       │   ├── theme_manager.py    # Theming and styling
│       │   ├── keyboard_manager.py # Keyboard shortcuts
│       │   ├── accessibility_manager.py # Accessibility
│       │   ├── responsive_layout.py # Responsive design
│       │   └── ui_polish.py        # UI coordination
│       ├── utils/                  # Utility modules
│       │   ├── __init__.py
│       │   ├── error_handling.py   # Error management
│       │   ├── performance_monitor.py # Performance tracking
│       │   ├── file_operations.py  # File utilities
│       │   └── config_manager.py   # Configuration
│       └── windows/                # UI windows and panels
│           ├── __init__.py
│           ├── main_window.py      # Main application window
│           └── panels/             # Individual UI panels
│               ├── __init__.py
│               ├── materials_panel.py
│               ├── mix_design_panel.py
│               ├── microstructure_panel.py
│               ├── hydration_panel.py
│               ├── file_management_panel.py
│               └── operations_monitoring_panel.py
├── tests/                          # Test suite
│   ├── conftest.py                 # Test configuration
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   ├── e2e/                        # End-to-end tests
│   └── performance/                # Performance tests
├── docs/                           # Documentation
│   ├── USER_MANUAL.md              # User guide
│   ├── INSTALLATION.md             # Installation guide
│   ├── DEVELOPER.md                # This file
│   └── API_REFERENCE.md            # API documentation
├── requirements.txt                # Production dependencies
├── requirements-dev.txt            # Development dependencies
├── setup.py                        # Package setup
├── pytest.ini                     # Pytest configuration
├── pyproject.toml                  # Project metadata
└── README.md                       # Project overview
```

---

## Core Components

### Application Class

The main application class (`src/app/application.py`) coordinates the entire application:

```python
class VCCTLApplication(Gtk.Application):
    """Main VCCTL application class."""
    
    def __init__(self):
        super().__init__(application_id="edu.tamu.vcctl")
        self.main_window = None
        self.service_container = None
    
    def do_activate(self):
        """Activate the application."""
        if not self.main_window:
            self._initialize_services()
            self._create_main_window()
        
        self.main_window.present()
    
    def _initialize_services(self):
        """Initialize service container and dependencies."""
        self.service_container = ServiceContainer()
        self.service_container.initialize()
```

### Service Container

Dependency injection container (`src/app/services/service_container.py`):

```python
class ServiceContainer:
    """Dependency injection container for services."""
    
    def __init__(self):
        self._services = {}
        self._singletons = {}
    
    def register(self, service_type, implementation, singleton=True):
        """Register a service implementation."""
        self._services[service_type] = implementation
        if singleton:
            self._singletons[service_type] = None
    
    def get(self, service_type):
        """Get service instance."""
        if service_type in self._singletons:
            if self._singletons[service_type] is None:
                self._singletons[service_type] = self._services[service_type]()
            return self._singletons[service_type]
        
        return self._services[service_type]()
```

---

## UI Framework

### GTK3 Integration

VCCTL uses GTK3 through PyGObject for native desktop integration:

```python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

class MaterialsPanel(Gtk.Box):
    """Materials management panel."""
    
    __gsignals__ = {
        'material-created': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'material-updated': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
    }
    
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.main_window = main_window
        self._setup_ui()
        self._connect_signals()
```

### UI Polish System

The UI polish system provides theming, accessibility, and responsive design:

```python
from app.ui import create_ui_polish_manager

# In main window initialization
self.ui_polish_manager = create_ui_polish_manager(self)

# Register widgets for enhanced features
self.ui_polish_manager.register_scientific_widget(
    'materials_panel', self.materials_panel,
    {
        'name': 'Materials Properties Panel',
        'description': 'Panel for managing cement materials',
        'tooltip': 'Add, edit, and view material properties'
    }
)
```

### Help System Integration

Contextual help and tooltips throughout the application:

```python
from app.help import create_help_system

# Initialize help system
self.help_manager, self.tooltip_manager = create_help_system(self)

# Show contextual help
def on_f1_pressed(self, widget, event):
    if event.keyval == Gdk.KEY_F1:
        current_tab = self.get_current_tab_name().lower()
        if current_tab == "materials":
            self.show_contextual_help("materials_panel")
        else:
            self._show_help_dialog()
        return True
```

---

## Data Models

### Pydantic Models

Data validation using Pydantic (`src/app/models/cement.py`):

```python
from pydantic import BaseModel, validator
from typing import Optional

class CementBase(BaseModel):
    """Base cement material model."""
    name: str
    type: str
    sio2: float
    al2o3: float
    fe2o3: float
    cao: float
    mgo: float
    so3: float
    blaine_fineness: Optional[float] = None
    density: float = 3.15
    
    @validator('sio2', 'al2o3', 'fe2o3', 'cao', 'mgo', 'so3')
    def validate_oxide_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Oxide percentage must be between 0 and 100')
        return v
    
    @validator('cao', always=True)
    def validate_total_composition(cls, v, values):
        """Validate total oxide composition sums to ~100%."""
        total = sum([
            values.get('sio2', 0),
            values.get('al2o3', 0),
            values.get('fe2o3', 0),
            v,  # cao
            values.get('mgo', 0),
            values.get('so3', 0)
        ])
        
        if not 98 <= total <= 102:
            raise ValueError(f'Total composition is {total:.1f}%, must be 98-102%')
        return v

class CementCreate(CementBase):
    """Model for creating new cement materials."""
    pass

class CementUpdate(CementBase):
    """Model for updating cement materials."""
    name: Optional[str] = None
    type: Optional[str] = None
    # ... other optional fields

class Cement(CementBase):
    """Complete cement model with database fields."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
```

### SQLAlchemy Models

Database models (`src/app/database/models.py`):

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class CementModel(Base):
    """SQLAlchemy model for cement materials."""
    __tablename__ = 'cements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    type = Column(String(50), nullable=False)
    sio2 = Column(Float, nullable=False)
    al2o3 = Column(Float, nullable=False)
    fe2o3 = Column(Float, nullable=False)
    cao = Column(Float, nullable=False)
    mgo = Column(Float, nullable=False)
    so3 = Column(Float, nullable=False)
    blaine_fineness = Column(Float)
    density = Column(Float, nullable=False, default=3.15)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def to_pydantic(self) -> 'Cement':
        """Convert to Pydantic model."""
        return Cement.from_orm(self)
```

---

## Service Layer

### Service Pattern Implementation

Business logic services (`src/app/services/cement_service.py`):

```python
class CementService:
    """Service for cement material operations."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
    
    def create(self, cement_create: CementCreate) -> Cement:
        """Create a new cement material."""
        try:
            # Validate the input
            self._validate_cement(cement_create)
            
            # Create database model
            cement_model = CementModel(**cement_create.dict())
            
            # Save to database
            with self.db_service.get_session() as session:
                session.add(cement_model)
                session.commit()
                session.refresh(cement_model)
                
                # Convert to Pydantic model
                return cement_model.to_pydantic()
                
        except Exception as e:
            self.logger.error(f"Failed to create cement: {e}")
            raise ServiceError(f"Could not create cement material: {e}")
    
    def get_all(self) -> List[Cement]:
        """Get all cement materials."""
        with self.db_service.get_read_only_session() as session:
            cement_models = session.query(CementModel).order_by(CementModel.name).all()
            return [model.to_pydantic() for model in cement_models]
    
    def _validate_cement(self, cement: CementCreate):
        """Additional business logic validation."""
        # Check for duplicate names
        if self.get_by_name(cement.name):
            raise ValidationError(f"Cement with name '{cement.name}' already exists")
        
        # Validate cement type
        valid_types = ['Type I', 'Type II', 'Type III', 'Type IV', 'Type V']
        if cement.type not in valid_types:
            raise ValidationError(f"Invalid cement type: {cement.type}")
```

### Error Handling

Centralized error management (`src/app/utils/error_handling.py`):

```python
class ErrorHandler(GObject.Object):
    """Centralized error handling system."""
    
    __gsignals__ = {
        'error-occurred': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
    }
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: str = None, 
                    severity: ErrorSeverity = ErrorSeverity.ERROR):
        """Handle application errors with user feedback."""
        
        # Log the error
        self.logger.error(f"Error in {context}: {error}", exc_info=True)
        
        # Create user-friendly message
        message = self._format_user_message(error, context)
        
        # Show appropriate dialog
        if severity == ErrorSeverity.CRITICAL:
            self._show_critical_error_dialog(message)
        elif severity == ErrorSeverity.ERROR:
            self._show_error_dialog(message)
        else:
            self._show_warning_dialog(message)
        
        # Emit signal for other components
        self.emit('error-occurred', {
            'error': error,
            'context': context,
            'severity': severity,
            'timestamp': datetime.now()
        })
```

---

## Database Integration

### Database Service

Database abstraction layer (`src/app/database/service.py`):

```python
class DatabaseService:
    """Database service with connection management."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or self._get_default_db_path()
        self.engine = None
        self.session_factory = None
        
    def initialize(self):
        """Initialize database connection and tables."""
        self.engine = create_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}  # SQLite specific
        )
        
        # Create session factory
        self.session_factory = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Run migrations
        self._run_migrations()
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup."""
        session = self.session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_read_only_session(self):
        """Get read-only session for queries."""
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()
```

### Migrations

Database schema migrations (`src/app/database/migrations/`):

```python
class MigrationManager:
    """Manages database schema migrations."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.migration_dir = Path(__file__).parent / "migrations"
    
    def migrate_to_latest(self) -> bool:
        """Apply all pending migrations."""
        current_version = self.get_current_schema_version()
        pending_migrations = self.get_pending_migrations()
        
        for migration in pending_migrations:
            if self._apply_migration(migration['version'], migration['sql']):
                self.logger.info(f"Applied migration {migration['version']}: {migration['name']}")
            else:
                self.logger.error(f"Failed to apply migration {migration['version']}")
                return False
        
        return True
```

---

## Testing Framework

### Test Structure

Comprehensive testing with pytest (`tests/conftest.py`):

```python
import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

@pytest.fixture(scope="session")
def gtk_test_environment():
    """Setup GTK test environment."""
    if 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':99'
    
    Gtk.init_check([])
    window = Gtk.OffscreenWindow()
    window.show()
    yield window
    window.destroy()

@pytest.fixture
def temp_directory():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def test_database():
    """Create in-memory test database."""
    from app.database.service import DatabaseService
    
    db_service = DatabaseService("sqlite:///:memory:")
    db_service.initialize()
    return db_service

@pytest.fixture
def sample_cement_data():
    """Sample cement data for testing."""
    return {
        'name': 'Test Cement',
        'type': 'Type I',
        'sio2': 20.5,
        'al2o3': 5.2,
        'fe2o3': 3.1,
        'cao': 65.0,
        'mgo': 2.8,
        'so3': 2.4,
        'blaine_fineness': 350.0,
        'density': 3.15
    }
```

### Unit Tests

Service layer testing (`tests/unit/test_cement_service.py`):

```python
@pytest.mark.unit
class TestCementService:
    """Unit tests for cement service."""
    
    def test_create_cement_success(self, test_database, sample_cement_data):
        """Test successful cement creation."""
        service = CementService(test_database)
        cement_create = CementCreate(**sample_cement_data)
        
        result = service.create(cement_create)
        
        assert result is not None
        assert result.name == sample_cement_data['name']
        assert result.id is not None
    
    def test_create_cement_duplicate_name(self, test_database, sample_cement_data):
        """Test cement creation with duplicate name fails."""
        service = CementService(test_database)
        cement_create = CementCreate(**sample_cement_data)
        
        # Create first cement
        service.create(cement_create)
        
        # Attempt to create duplicate should fail
        with pytest.raises(ValidationError, match="already exists"):
            service.create(cement_create)
```

### Integration Tests

UI component testing (`tests/integration/test_ui_components.py`):

```python
@pytest.mark.integration
@pytest.mark.gui
class TestUIComponents:
    """Integration tests for UI components."""
    
    def test_materials_panel_creation(self, gtk_test_environment):
        """Test materials panel can be created and displayed."""
        from app.windows.panels import MaterialsPanel
        
        main_window = Mock()
        panel = MaterialsPanel(main_window)
        
        assert panel is not None
        assert isinstance(panel, Gtk.Widget)
    
    def test_help_dialog_functionality(self, gtk_test_environment):
        """Test help dialog opens and displays content."""
        from app.help import HelpDialog, HelpManager
        
        help_manager = HelpManager()
        dialog = HelpDialog(None, help_manager)
        
        # Test showing different topics
        dialog.show_topic("overview")
        assert dialog.current_topic is not None
        
        # Test search functionality
        dialog.search_topics("cement")
        # Verify search results are displayed
```

### End-to-End Tests

Complete workflow testing (`tests/e2e/test_complete_workflows.py`):

```python
@pytest.mark.e2e
class TestCompleteWorkflows:
    """End-to-end workflow tests."""
    
    def test_material_to_simulation_workflow(self, vcctl_app, workflow_data):
        """Test complete workflow from material creation to simulation."""
        
        # Step 1: Create materials
        cement_created = self._create_cement_material(vcctl_app, workflow_data['cement'])
        assert cement_created is True
        
        # Step 2: Design mix
        mix_created = self._design_concrete_mix(vcctl_app, workflow_data['mix_design'])
        assert mix_created is True
        
        # Step 3: Generate microstructure
        microstructure_generated = self._generate_microstructure(vcctl_app, workflow_data)
        assert microstructure_generated is True
        
        # Step 4: Run simulation
        simulation_completed = self._run_hydration_simulation(vcctl_app, workflow_data)
        assert simulation_completed is True
```

---

## Build and Deployment

### Package Configuration

Setup configuration (`setup.py`):

```python
from setuptools import setup, find_packages

setup(
    name="vcctl-desktop",
    version="2.0.0",
    description="Virtual Cement and Concrete Testing Laboratory - Desktop Application",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="NIST Building and Fire Research Laboratory",
    author_email="vcctl@nist.gov",
    url="https://github.com/usnistgov/vcctl",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "PyGObject>=3.30.0",
        "pydantic>=1.8.0",
        "SQLAlchemy>=1.4.0",
        "numpy>=1.19.0",
        "scipy>=1.6.0",
        "matplotlib>=3.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
            "pre-commit>=2.10",
        ]
    },
    entry_points={
        "console_scripts": [
            "vcctl=app.main:main",
        ],
        "gui_scripts": [
            "vcctl-gui=app.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: Public Domain",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering",
    ],
)
```

### Build Scripts

Automated build process (`scripts/build.py`):

```python
#!/usr/bin/env python3
"""Build script for VCCTL desktop application."""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run test suite."""
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("Tests failed!")
        print(result.stdout)
        print(result.stderr)
        return False
    return True

def build_package():
    """Build distribution packages."""
    subprocess.run([sys.executable, "-m", "build"], check=True)

def create_appimage():
    """Create AppImage for Linux distribution."""
    # AppImage creation logic
    pass

def create_windows_installer():
    """Create Windows installer using PyInstaller."""
    subprocess.run([
        "pyinstaller",
        "--windowed",
        "--onefile",
        "--add-data", "src/app/ui/themes:themes",
        "--add-data", "docs:docs",
        "--icon", "resources/icon.ico",
        "src/app/main.py"
    ], check=True)

if __name__ == "__main__":
    print("Running tests...")
    if not run_tests():
        sys.exit(1)
    
    print("Building package...")
    build_package()
    
    print("Build completed successfully!")
```

### Continuous Integration

GitHub Actions workflow (`.github/workflows/ci.yml`):

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.8, 3.9, '3.10']
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install system dependencies (Ubuntu)
      if: matrix.os == 'ubuntu-latest'
      run: |
        sudo apt-get update
        sudo apt-get install -y libgirepository1.0-dev pkg-config
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
        pip install -e .
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

---

## Contributing Guidelines

### Code Style

- **Formatting**: Use Black for code formatting
- **Linting**: Follow flake8 rules with line length 88
- **Type Hints**: Use type hints for all public APIs
- **Docstrings**: Google-style docstrings for all modules, classes, and functions

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(materials): add support for supplementary cementitious materials

- Add fly ash and slag material types
- Implement pozzolanic activity calculations
- Update validation rules for SCM compositions

Closes #123
```

### Pull Request Process

1. **Fork Repository**: Create personal fork on GitHub
2. **Create Branch**: Use descriptive branch names (`feature/scm-support`)
3. **Make Changes**: Follow coding standards and add tests
4. **Run Tests**: Ensure all tests pass locally
5. **Submit PR**: Create pull request with clear description
6. **Code Review**: Address reviewer feedback
7. **Merge**: Squash and merge when approved

### Testing Requirements

All contributions must include appropriate tests:

- **New Features**: Unit tests, integration tests, documentation
- **Bug Fixes**: Test that reproduces the bug and verifies the fix
- **UI Changes**: UI tests and accessibility verification
- **API Changes**: API tests and documentation updates

---

## API Reference

### Core Services

#### CementService

```python
class CementService:
    def create(self, cement_create: CementCreate) -> Cement:
        """Create new cement material."""
    
    def get_all(self) -> List[Cement]:
        """Get all cement materials."""
    
    def get_by_id(self, cement_id: int) -> Optional[Cement]:
        """Get cement by ID."""
    
    def update(self, cement_id: int, cement_update: CementUpdate) -> Cement:
        """Update cement material."""
    
    def delete(self, cement_id: int) -> bool:
        """Delete cement material."""
```

#### DatabaseService

```python
class DatabaseService:
    def initialize(self) -> None:
        """Initialize database connection."""
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session."""
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health."""
```

### UI Components

#### HelpManager

```python
class HelpManager(GObject.Object):
    def show_help(self, topic_id: str = None, context: str = None) -> None:
        """Show help dialog."""
    
    def search_topics(self, query: str) -> List[HelpTopic]:
        """Search help topics."""
    
    def get_contextual_help(self, context: str) -> Optional[HelpTopic]:
        """Get contextual help."""
```

#### TooltipManager

```python
class TooltipManager(GObject.Object):
    def apply_tooltip(self, widget: Gtk.Widget, widget_id: str) -> None:
        """Apply tooltip to widget."""
    
    def create_validation_tooltip(self, field_name: str, error_message: str) -> TooltipInfo:
        """Create validation error tooltip."""
```

### Data Models

#### Cement Models

```python
class CementCreate(BaseModel):
    name: str
    type: str
    sio2: float
    al2o3: float
    fe2o3: float
    cao: float
    mgo: float
    so3: float
    blaine_fineness: Optional[float] = None
    density: float = 3.15

class Cement(CementCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
```

### Signals and Events

#### Application Signals

```python
# Material events
'material-created': (object,)    # Emitted when material is created
'material-updated': (object,)    # Emitted when material is updated
'material-deleted': (int,)       # Emitted when material is deleted

# Simulation events
'simulation-started': (str,)     # Emitted when simulation starts
'simulation-progress': (float,)  # Emitted during simulation progress
'simulation-completed': (object,) # Emitted when simulation completes

# Error events
'error-occurred': (object,)      # Emitted when error occurs
```

---

## Performance Considerations

### Memory Management

- Use weak references for circular dependencies
- Implement proper cleanup in window/panel destructors
- Monitor memory usage during long simulations
- Use generators for large datasets

### Database Optimization

- Use read-only sessions for queries
- Implement connection pooling
- Add database indexes for frequently queried fields
- Use bulk operations for large datasets

### UI Responsiveness

- Use threading for long-running operations
- Implement progress indicators for user feedback
- Use lazy loading for large UI components
- Optimize GTK widget creation and destruction

---

## Security Considerations

### Input Validation

- Validate all user inputs using Pydantic models
- Sanitize file paths and names
- Implement size limits for file uploads
- Check file types and signatures

### Data Protection

- Encrypt sensitive configuration data
- Use secure file permissions
- Implement audit logging for critical operations
- Follow principle of least privilege

---

## Debugging and Profiling

### Logging Configuration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vcctl.log'),
        logging.StreamHandler()
    ]
)

# Logger usage
logger = logging.getLogger(__name__)
logger.info("Operation completed successfully")
logger.error("Error occurred", exc_info=True)
```

### Performance Profiling

```python
from app.utils.performance_monitor import profile_function

@profile_function
def expensive_operation():
    """Function that will be profiled."""
    # Implementation
    pass

# Or use context manager
with PerformanceTimer() as timer:
    # Code to profile
    pass

print(f"Operation took {timer.elapsed:.3f} seconds")
```

### Memory Profiling

```python
import tracemalloc

# Start tracing
tracemalloc.start()

# Your code here

# Get current memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
```

---

## Future Development

### Planned Features

- Advanced visualization capabilities
- Cloud simulation support
- Plugin architecture
- Advanced material libraries
- Machine learning integration

### Architecture Improvements

- Microservices architecture for scalability
- Event sourcing for data consistency
- CQRS pattern for read/write separation
- GraphQL API for flexible data access

### Technology Upgrades

- GTK4 migration for improved performance
- Async/await for better concurrency
- WebAssembly for browser compatibility
- Container deployment options

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Maintained by**: VCCTL Development Team, NIST Building and Fire Research Laboratory