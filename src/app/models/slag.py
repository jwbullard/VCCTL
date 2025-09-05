#!/usr/bin/env python3
"""
Slag Model for VCCTL

Represents slag materials with composition, reactivity, and hydration properties.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, Text
from pydantic import BaseModel, Field, field_validator, model_validator

from app.database.base import Base


class Slag(Base):
    """
    Slag model representing ground granulated blast-furnace slag (GGBS).
    
    Contains slag composition data, molecular properties,
    reactivity parameters, and hydration product characteristics.
    """
    
    __tablename__ = 'slag'
    
    # Use integer ID as primary key (inherited from Base)
    # Name is now just a regular field that can be updated  
    name = Column(String(64), nullable=False, unique=True)
    
    # Physical properties
    specific_gravity = Column(Float, nullable=True, default=2.87,
                            doc="Specific gravity of slag material")
    
    # Particle size distribution reference
    psd = Column(String(64), nullable=True, default='cement141',
                doc="Particle size distribution reference")
    
    psd_custom_points = Column(Text, nullable=True, 
                              doc="Custom PSD points stored as JSON")
    
    # Complete PSD parameters (unified with cement model)
    psd_mode = Column(String(64), nullable=True, default='log_normal',
                     doc="PSD mode (rosin_rammler, log_normal, fuller, custom)")
    psd_d50 = Column(Float, nullable=True, default=15.0,
                    doc="PSD D50 parameter (μm) for Rosin-Rammler")
    psd_n = Column(Float, nullable=True, default=1.4,
                  doc="PSD n parameter for Rosin-Rammler")
    psd_dmax = Column(Float, nullable=True, default=75.0,
                     doc="PSD Dmax parameter (μm)")
    psd_median = Column(Float, nullable=True, default=15.0,
                       doc="Median particle size (μm) for log-normal distribution")
    psd_spread = Column(Float, nullable=True, default=1.4,
                       doc="PSD distribution spread parameter for log-normal distribution")
    psd_exponent = Column(Float, nullable=True, default=0.5,
                         doc="PSD exponent parameter for Fuller-Thompson")
    
    # Basic slag properties
    glass_content = Column(Float, nullable=True, default=95.0,
                          doc="Glass content percentage")
    activity_index = Column(Float, nullable=True, default=95.0,
                           doc="Activity index percentage")
    
    # Chemical composition (oxide content) - typical GGBS composition totaling 100%
    sio2_content = Column(Float, nullable=True, default=35.0,
                         doc="SiO2 content percentage")
    cao_content = Column(Float, nullable=True, default=40.0,
                        doc="CaO content percentage")
    al2o3_content = Column(Float, nullable=True, default=12.0,
                          doc="Al2O3 content percentage")
    mgo_content = Column(Float, nullable=True, default=8.0,
                        doc="MgO content percentage")
    fe2o3_content = Column(Float, nullable=True, default=1.0,
                          doc="Fe2O3 content percentage")
    so3_content = Column(Float, nullable=True, default=4.0,
                        doc="SO3 content percentage")
    
    # Reaction parameters
    activation_energy = Column(Float, nullable=True, default=54000.0,
                              doc="Activation energy (J/mol)")
    reactivity_factor = Column(Float, nullable=True, default=1.0,
                              doc="Reactivity factor")
    rate_constant = Column(Float, nullable=True, default=1e-6,
                          doc="Rate constant (1/s)")
    
    # Molecular and chemical properties
    molecular_mass = Column(Float, nullable=True,
                          doc="Molecular mass of slag")
    casi_mol_ratio = Column(Float, nullable=True,
                          doc="CaO/SiO2 molar ratio")
    si_per_mole = Column(Float, nullable=True,
                        doc="Silicon atoms per mole of slag")
    base_slag_reactivity = Column(Float, nullable=True,
                                doc="Base reactivity of slag")
    c3a_per_mole = Column(Float, nullable=True,
                         doc="C3A content per mole")
    
    # Hydration product (HP) properties
    hp_molecular_mass = Column(Float, nullable=True,
                             doc="Hydration product molecular mass")
    hp_density = Column(Float, nullable=True,
                       doc="Hydration product density")
    hp_casi_mol_ratio = Column(Float, nullable=True,
                             doc="Hydration product CaO/SiO2 molar ratio")
    hp_h2o_si_mol_ratio = Column(Float, nullable=True,
                               doc="Hydration product H2O/SiO2 molar ratio")
    
    # Description and metadata
    description = Column(String, nullable=True,
                        doc="Slag description and notes")
    source = Column(String(255), nullable=True, doc="Material source")
    notes = Column(String(1000), nullable=True, doc="Additional notes")
    
    def __repr__(self) -> str:
        """String representation of the slag."""
        return f"<Slag(name='{self.name}', specific_gravity={self.specific_gravity})>"
    
    @property
    def molecular_properties(self) -> dict:
        """Get all molecular properties as a dictionary."""
        return {
            'molecular_mass': self.molecular_mass,
            'casi_mol_ratio': self.casi_mol_ratio,
            'si_per_mole': self.si_per_mole,
            'c3a_per_mole': self.c3a_per_mole
        }
    
    @property
    def hydration_product_properties(self) -> dict:
        """Get all hydration product properties as a dictionary."""
        return {
            'hp_molecular_mass': self.hp_molecular_mass,
            'hp_density': self.hp_density,
            'hp_casi_mol_ratio': self.hp_casi_mol_ratio,
            'hp_h2o_si_mol_ratio': self.hp_h2o_si_mol_ratio
        }
    
    @property
    def has_complete_molecular_data(self) -> bool:
        """Check if slag has complete molecular composition data."""
        return all([
            self.molecular_mass is not None,
            self.casi_mol_ratio is not None,
            self.si_per_mole is not None
        ])
    
    @property
    def has_complete_hp_data(self) -> bool:
        """Check if slag has complete hydration product data."""
        return all([
            self.hp_molecular_mass is not None,
            self.hp_density is not None,
            self.hp_casi_mol_ratio is not None,
            self.hp_h2o_si_mol_ratio is not None
        ])
    
    @property
    def has_reactivity_data(self) -> bool:
        """Check if slag has reactivity data."""
        return self.base_slag_reactivity is not None
    
    def calculate_activation_energy(self, temperature: float = 25.0) -> Optional[float]:
        """
        Calculate activation energy based on slag properties.
        
        This is a placeholder for the actual calculation that would
        be based on the slag's chemical composition and reactivity.
        
        Args:
            temperature: Temperature in Celsius
            
        Returns:
            Calculated activation energy or None if insufficient data
        """
        if not self.has_reactivity_data or not self.base_slag_reactivity:
            return None
        
        # Placeholder calculation - actual implementation would be more complex
        # and based on scientific models for slag hydration kinetics
        base_activation = 50000  # J/mol (typical for cementitious materials)
        reactivity_factor = self.base_slag_reactivity if self.base_slag_reactivity > 0 else 1.0
        
        # Adjust based on reactivity (higher reactivity = lower activation energy)
        activation_energy = base_activation / reactivity_factor
        
        return activation_energy
    
    def validate_molecular_ratios(self) -> bool:
        """Validate that molecular ratios are reasonable."""
        if self.casi_mol_ratio is not None and (self.casi_mol_ratio < 0 or self.casi_mol_ratio > 10):
            return False
        
        if self.hp_casi_mol_ratio is not None and (self.hp_casi_mol_ratio < 0 or self.hp_casi_mol_ratio > 10):
            return False
        
        if self.hp_h2o_si_mol_ratio is not None and (self.hp_h2o_si_mol_ratio < 0 or self.hp_h2o_si_mol_ratio > 5):
            return False
        
        return True


class SlagCreate(BaseModel):
    """Pydantic model for creating slag instances."""
    
    name: str = Field(..., max_length=64, description="Slag name (unique identifier)")
    specific_gravity: Optional[float] = Field(2.87, gt=0.0, description="Specific gravity")
    psd: Optional[str] = Field('cement141', max_length=64,
                              description="Particle size distribution reference")
    psd_custom_points: Optional[str] = Field(None, description="Custom PSD points stored as JSON")
    
    # Complete PSD parameters (unified with cement model)
    psd_mode: Optional[str] = Field('log_normal', max_length=64, 
                                   description="PSD mode (rosin_rammler, log_normal, fuller, custom)")
    psd_d50: Optional[float] = Field(15.0, gt=0.0, description="PSD D50 parameter (μm)")
    psd_n: Optional[float] = Field(1.4, gt=0.0, description="PSD n parameter")
    psd_dmax: Optional[float] = Field(75.0, gt=0.0, description="PSD Dmax parameter (μm)")
    psd_median: Optional[float] = Field(15.0, gt=0.0, description="Median particle size (μm)")
    psd_spread: Optional[float] = Field(1.4, gt=0.0, description="PSD distribution spread parameter")
    psd_exponent: Optional[float] = Field(0.5, gt=0.0, description="PSD exponent parameter")
    
    # Basic slag properties
    glass_content: Optional[float] = Field(95.0, ge=85.0, le=100.0, description="Glass content percentage")
    activity_index: Optional[float] = Field(95.0, ge=50.0, le=150.0, description="Activity index percentage")
    
    # Chemical composition (oxide content) - typical GGBS composition totaling 100%
    sio2_content: Optional[float] = Field(35.0, ge=0.0, le=100.0, description="SiO2 content percentage")
    cao_content: Optional[float] = Field(40.0, ge=0.0, le=100.0, description="CaO content percentage")
    al2o3_content: Optional[float] = Field(12.0, ge=0.0, le=100.0, description="Al2O3 content percentage")
    mgo_content: Optional[float] = Field(8.0, ge=0.0, le=100.0, description="MgO content percentage")
    fe2o3_content: Optional[float] = Field(1.0, ge=0.0, le=100.0, description="Fe2O3 content percentage")
    so3_content: Optional[float] = Field(4.0, ge=0.0, le=100.0, description="SO3 content percentage")
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(54000.0, gt=0.0, description="Activation energy (J/mol)")
    reactivity_factor: Optional[float] = Field(1.0, ge=0.1, le=2.0, description="Reactivity factor")
    rate_constant: Optional[float] = Field(1e-6, ge=1e-8, le=1e-4, description="Rate constant (1/s)")
    
    # Molecular properties
    molecular_mass: Optional[float] = Field(None, gt=0.0, description="Molecular mass")
    casi_mol_ratio: Optional[float] = Field(None, ge=0.0, le=10.0,
                                          description="CaO/SiO2 molar ratio")
    si_per_mole: Optional[float] = Field(None, gt=0.0, description="Silicon atoms per mole")
    base_slag_reactivity: Optional[float] = Field(None, gt=0.0,
                                                 description="Base reactivity")
    c3a_per_mole: Optional[float] = Field(None, ge=0.0, description="C3A per mole")
    
    # Hydration product properties
    hp_molecular_mass: Optional[float] = Field(None, gt=0.0,
                                             description="HP molecular mass")
    hp_density: Optional[float] = Field(None, gt=0.0, description="HP density")
    hp_casi_mol_ratio: Optional[float] = Field(None, ge=0.0, le=10.0,
                                             description="HP CaO/SiO2 ratio")
    hp_h2o_si_mol_ratio: Optional[float] = Field(None, ge=0.0, le=5.0,
                                                description="HP H2O/SiO2 ratio")
    
    description: Optional[str] = Field(None, description="Slag description")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate slag name."""
        if not v or not v.strip():
            raise ValueError('Slag name cannot be empty')
        return v.strip()
    
    @field_validator('specific_gravity')
    @classmethod
    def validate_specific_gravity(cls, v):
        """Validate specific gravity."""
        if v is not None and v <= 0:
            raise ValueError('Specific gravity must be positive')
        return v


class SlagUpdate(BaseModel):
    """Pydantic model for updating slag instances."""
    
    specific_gravity: Optional[float] = Field(None, gt=0.0, description="Specific gravity")
    psd: Optional[str] = Field(None, max_length=64,
                              description="Particle size distribution reference")
    psd_custom_points: Optional[str] = Field(None, description="Custom PSD points stored as JSON")
    
    # PSD parameters for log-normal distribution
    psd_median: Optional[float] = Field(None, gt=0.0, description="Median particle size (μm)")
    psd_spread: Optional[float] = Field(None, gt=0.0, description="PSD distribution spread parameter")
    
    # Basic slag properties
    glass_content: Optional[float] = Field(None, ge=85.0, le=100.0, description="Glass content percentage")
    activity_index: Optional[float] = Field(None, ge=50.0, le=150.0, description="Activity index percentage")
    
    # Chemical composition (oxide content)
    sio2_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="SiO2 content percentage")
    cao_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="CaO content percentage")
    al2o3_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="Al2O3 content percentage")
    mgo_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="MgO content percentage")
    fe2o3_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="Fe2O3 content percentage")
    so3_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="SO3 content percentage")
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(None, gt=0.0, description="Activation energy (J/mol)")
    reactivity_factor: Optional[float] = Field(None, ge=0.1, le=2.0, description="Reactivity factor")
    rate_constant: Optional[float] = Field(None, ge=1e-8, le=1e-4, description="Rate constant (1/s)")
    
    # Molecular properties
    molecular_mass: Optional[float] = Field(None, gt=0.0, description="Molecular mass")
    casi_mol_ratio: Optional[float] = Field(None, ge=0.0, le=10.0,
                                          description="CaO/SiO2 molar ratio")
    si_per_mole: Optional[float] = Field(None, gt=0.0, description="Silicon atoms per mole")
    base_slag_reactivity: Optional[float] = Field(None, gt=0.0,
                                                 description="Base reactivity")
    c3a_per_mole: Optional[float] = Field(None, ge=0.0, description="C3A per mole")
    
    # Hydration product properties
    hp_molecular_mass: Optional[float] = Field(None, gt=0.0,
                                             description="HP molecular mass")
    hp_density: Optional[float] = Field(None, gt=0.0, description="HP density")
    hp_casi_mol_ratio: Optional[float] = Field(None, ge=0.0, le=10.0,
                                             description="HP CaO/SiO2 ratio")
    hp_h2o_si_mol_ratio: Optional[float] = Field(None, ge=0.0, le=5.0,
                                                description="HP H2O/SiO2 ratio")
    
    description: Optional[str] = Field(None, description="Slag description")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class SlagResponse(BaseModel):
    """Pydantic model for slag API responses."""
    
    name: str
    specific_gravity: Optional[float]
    psd: Optional[str]
    
    # PSD parameters
    psd_median: Optional[float]
    psd_spread: Optional[float]
    
    # Basic slag properties
    glass_content: Optional[float]
    activity_index: Optional[float]
    
    # Chemical composition
    sio2_content: Optional[float]
    cao_content: Optional[float]
    al2o3_content: Optional[float]
    mgo_content: Optional[float]
    fe2o3_content: Optional[float]
    so3_content: Optional[float]
    
    # Reaction parameters
    activation_energy: Optional[float]
    reactivity_factor: Optional[float]
    rate_constant: Optional[float]
    
    molecular_mass: Optional[float]
    casi_mol_ratio: Optional[float]
    si_per_mole: Optional[float]
    base_slag_reactivity: Optional[float]
    c3a_per_mole: Optional[float]
    hp_molecular_mass: Optional[float]
    hp_density: Optional[float]
    hp_casi_mol_ratio: Optional[float]
    hp_h2o_si_mol_ratio: Optional[float]
    description: Optional[str]
    source: Optional[str]
    notes: Optional[str]
    has_complete_molecular_data: bool
    has_complete_hp_data: bool
    has_reactivity_data: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True