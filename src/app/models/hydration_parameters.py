#!/usr/bin/env python3
"""
Hydration Parameters Model for VCCTL

Stores parameters for cement hydration simulations.
Uses JSON blob for storing 372 parameters from default.prm file.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.hybrid import hybrid_property

from app.database.base import Base


class HydrationParameters(Base):
    """
    Hydration parameters model for storing cement hydration simulation parameters.
    
    Stores parameter sets as JSON blobs to handle the 372 parameters efficiently.
    Initially contains 'portland_cement_standard' parameter set loaded from default.prm.
    """
    
    __tablename__ = 'hydration_parameters'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False, 
                 doc="Parameter set name (e.g., 'portland_cement_standard')")
    parameters = Column(JSON, nullable=False, 
                       doc="JSON object containing all hydration parameters")
    description = Column(String(255), nullable=True,
                        doc="Description of the parameter set")
    created_at = Column(DateTime, default=datetime.utcnow,
                       doc="When this parameter set was created")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                       doc="When this parameter set was last updated")
    
    def __repr__(self) -> str:
        """String representation of the hydration parameters."""
        param_count = len(self.parameters) if self.parameters else 0
        return f"<HydrationParameters(name='{self.name}', parameters_count={param_count})>"
    
    @hybrid_property
    def parameter_count(self) -> int:
        """Get the number of parameters in this set."""
        return len(self.parameters) if self.parameters else 0
    
    def get_parameter(self, param_name: str, default=None):
        """Get a specific parameter value by name."""
        if not self.parameters:
            return default
        return self.parameters.get(param_name, default)
    
    def set_parameter(self, param_name: str, value):
        """Set a specific parameter value."""
        if self.parameters is None:
            self.parameters = {}
        self.parameters[param_name] = value
        self.updated_at = datetime.utcnow()
    
    def update_parameters(self, new_parameters: Dict[str, Any]):
        """Update multiple parameters at once."""
        if self.parameters is None:
            self.parameters = {}
        self.parameters.update(new_parameters)
        self.updated_at = datetime.utcnow()
    
    def export_to_prm_format(self) -> str:
        """
        Export parameters to .prm file format (tab-separated name-value pairs).
        
        Returns:
            String content ready to write to a .prm file
        """
        if not self.parameters:
            return ""
        
        lines = []
        for param_name, value in self.parameters.items():
            lines.append(f"{param_name}\t{value}")
        
        return "\n".join(lines)
    
    def export_to_file(self, filepath: str):
        """
        Export parameters to a .prm file.
        
        Args:
            filepath: Path to the output .prm file
        """
        content = self.export_to_prm_format()
        with open(filepath, 'w') as f:
            f.write(content)
    
    @classmethod
    def create_from_prm_file(cls, name: str, filepath: str, description: str = None):
        """
        Create a new HydrationParameters instance from a .prm file.
        
        Args:
            name: Name for the parameter set
            filepath: Path to the .prm file to read
            description: Optional description for the parameter set
            
        Returns:
            New HydrationParameters instance
        """
        parameters = {}
        
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 2:
                    param_name = parts[0]
                    param_value_str = parts[1]
                    
                    # Try to convert to appropriate type
                    try:
                        # Try integer first
                        if '.' not in param_value_str:
                            param_value = int(param_value_str)
                        else:
                            # Try float
                            param_value = float(param_value_str)
                    except ValueError:
                        # Keep as string if conversion fails
                        param_value = param_value_str
                    
                    parameters[param_name] = param_value
                else:
                    print(f"Warning: Skipping malformed line {line_num}: {line}")
        
        return cls(
            name=name,
            parameters=parameters,
            description=description
        )