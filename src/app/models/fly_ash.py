#!/usr/bin/env python3
"""
Fly Ash Model for VCCTL

Represents fly ash materials with composition, properties, and phase distributions.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, Integer, CheckConstraint, Text
from pydantic import BaseModel, Field, field_validator, model_validator

from app.database.base import Base


class FlyAsh(Base):
    """
    Fly ash model representing supplementary cementitious materials.
    
    Contains fly ash composition data, phase distributions,
    and physical properties like specific gravity.
    """
    
    __tablename__ = 'fly_ash'
    
    # Use integer ID as primary key (inherited from Base)
    # Name is now just a regular field that can be updated
    name = Column(String(64), nullable=False, unique=True)
    
    # Physical properties
    specific_gravity = Column(Float, nullable=True, default=2.77, 
                            doc="Specific gravity of fly ash material")
    
    # Particle size distribution reference
    psd = Column(String(64), nullable=True, default='cement141',
                doc="Particle size distribution reference")
    
    psd_custom_points = Column(Text, nullable=True, 
                              doc="Custom PSD points stored as JSON")
    
    # Complete PSD parameters (unified with cement model)
    psd_mode = Column(String(64), nullable=True, default='log_normal',
                     doc="PSD mode (rosin_rammler, log_normal, fuller, custom)")
    psd_d50 = Column(Float, nullable=True, default=5.0,
                    doc="PSD D50 parameter (μm) for Rosin-Rammler")
    psd_n = Column(Float, nullable=True, default=2.0,
                  doc="PSD n parameter for Rosin-Rammler")
    psd_dmax = Column(Float, nullable=True, default=75.0,
                     doc="PSD Dmax parameter (μm)")
    psd_median = Column(Float, nullable=True, default=5.0,
                       doc="Median particle size (μm) for log-normal distribution")
    psd_spread = Column(Float, nullable=True, default=2.0,
                       doc="PSD distribution spread parameter for log-normal distribution")
    psd_exponent = Column(Float, nullable=True, default=0.5,
                         doc="PSD exponent parameter for Fuller-Thompson")
    
    # Phase distribution parameters
    distribute_phases_by = Column(Integer, nullable=True,
                                doc="Method for phase distribution")
    
    # Phase fractions (mass fractions)
    aluminosilicate_glass_fraction = Column(Float, nullable=True,
                                          doc="Aluminosilicate glass mass fraction")
    calcium_aluminum_disilicate_fraction = Column(Float, nullable=True,
                                                 doc="Calcium aluminum disilicate mass fraction")
    tricalcium_aluminate_fraction = Column(Float, nullable=True,
                                         doc="Tricalcium aluminate mass fraction")
    calcium_chloride_fraction = Column(Float, nullable=True,
                                     doc="Calcium chloride mass fraction")
    silica_fraction = Column(Float, nullable=True,
                           doc="Silica mass fraction")
    anhydrate_fraction = Column(Float, nullable=True,
                              doc="Anhydrate mass fraction")
    
    # Chemical composition (oxide content) - typical Class F fly ash composition
    sio2_content = Column(Float, nullable=True, default=52.0,
                         doc="SiO2 content percentage")
    al2o3_content = Column(Float, nullable=True, default=23.0,
                          doc="Al2O3 content percentage")
    fe2o3_content = Column(Float, nullable=True, default=11.0,
                          doc="Fe2O3 content percentage")
    cao_content = Column(Float, nullable=True, default=5.0,
                        doc="CaO content percentage")
    mgo_content = Column(Float, nullable=True, default=2.0,
                        doc="MgO content percentage")
    so3_content = Column(Float, nullable=True, default=1.0,
                        doc="SO3 content percentage")
    
    # Physical properties
    loi = Column(Float, nullable=True, default=3.0,
                doc="Loss on ignition (unburned carbon content) percentage")
    fineness_45um = Column(Float, nullable=True, default=20.0,
                          doc="Fineness - percent retained on 45μm sieve")
    
    # Alkali characteristics
    na2o = Column(Float, nullable=True, default=1.2,
                 doc="Na2O content percentage")
    k2o = Column(Float, nullable=True, default=2.1,
                doc="K2O content percentage")
    na2o_equivalent = Column(Float, nullable=True,
                           doc="Calculated Na2O equivalent percentage")
    
    # Classification properties
    astm_class = Column(String(20), nullable=True, default='class_f',
                       doc="ASTM classification (class_f, class_c, class_n)")
    activity_index = Column(Float, nullable=True, default=85.0,
                          doc="Activity index percentage")
    pozzolanic_activity = Column(Float, nullable=True, default=75.0,
                               doc="Pozzolanic activity index percentage")
    
    # Reaction parameters
    activation_energy = Column(Float, nullable=True, default=54000.0,
                              doc="Activation energy (J/mol)")
    
    # Description and metadata
    description = Column(String(512), nullable=True,
                        doc="Fly ash description and notes")
    source = Column(String(255), nullable=True, doc="Material source")
    notes = Column(String(1000), nullable=True, doc="Additional notes")
    
    # Add constraint for specific gravity
    __table_args__ = (
        CheckConstraint('specific_gravity >= 0.0', name='check_specific_gravity_positive'),
    )
    
    def __repr__(self) -> str:
        """String representation of the fly ash."""
        return f"<FlyAsh(name='{self.name}', specific_gravity={self.specific_gravity})>"
    
    def build_phase_distribution_input(self) -> str:
        """
        Build phase distribution input string for simulation.
        
        Returns a formatted string with phase distribution parameters
        matching the Java implementation.
        """
        return (
            f"{self.distribute_phases_by or 0}\n"
            f"{self.aluminosilicate_glass_fraction or 0.0}\n"
            f"{self.calcium_aluminum_disilicate_fraction or 0.0}\n"
            f"{self.tricalcium_aluminate_fraction or 0.0}\n"
            f"{self.calcium_chloride_fraction or 0.0}\n"
            f"{self.silica_fraction or 0.0}\n"
            f"{self.anhydrate_fraction or 0.0}\n"
        )
    
    @property
    def phase_fractions(self) -> dict:
        """Get all phase fractions as a dictionary."""
        return {
            'aluminosilicate_glass': self.aluminosilicate_glass_fraction,
            'calcium_aluminum_disilicate': self.calcium_aluminum_disilicate_fraction,
            'tricalcium_aluminate': self.tricalcium_aluminate_fraction,
            'calcium_chloride': self.calcium_chloride_fraction,
            'silica': self.silica_fraction,
            'anhydrate': self.anhydrate_fraction
        }
    
    @property
    def total_phase_fraction(self) -> Optional[float]:
        """Calculate total phase fraction if all values are present."""
        fractions = [
            self.aluminosilicate_glass_fraction,
            self.calcium_aluminum_disilicate_fraction,
            self.tricalcium_aluminate_fraction,
            self.calcium_chloride_fraction,
            self.silica_fraction,
            self.anhydrate_fraction
        ]
        
        valid_fractions = [f for f in fractions if f is not None]
        if len(valid_fractions) == len(fractions):
            return sum(valid_fractions)
        return None
    
    @property
    def has_complete_phase_data(self) -> bool:
        """Check if fly ash has complete phase composition data."""
        fractions = [
            self.aluminosilicate_glass_fraction,
            self.calcium_aluminum_disilicate_fraction,
            self.tricalcium_aluminate_fraction,
            self.calcium_chloride_fraction,
            self.silica_fraction,
            self.anhydrate_fraction
        ]
        return all(f is not None for f in fractions)
    
    def validate_phase_fractions(self) -> bool:
        """Validate that phase fractions are reasonable (0-1 range and sum <= 1)."""
        fractions = [
            self.aluminosilicate_glass_fraction,
            self.calcium_aluminum_disilicate_fraction,
            self.tricalcium_aluminate_fraction,
            self.calcium_chloride_fraction,
            self.silica_fraction,
            self.anhydrate_fraction
        ]
        
        valid_fractions = [f for f in fractions if f is not None]
        
        if not valid_fractions:
            return True  # No fractions to validate
        
        # Check individual fractions are in valid range
        if any(f < 0 or f > 1 for f in valid_fractions):
            return False
        
        # Check total doesn't exceed 1.0 if we have a significant number of fractions
        if len(valid_fractions) >= 3 and sum(valid_fractions) > 1.0:
            return False
        
        return True


class FlyAshCreate(BaseModel):
    """Pydantic model for creating fly ash instances."""
    
    name: str = Field(..., max_length=64, description="Fly ash name (unique identifier)")
    specific_gravity: Optional[float] = Field(2.77, ge=0.0, description="Specific gravity")
    psd: Optional[str] = Field('cement141', max_length=64, 
                              description="Particle size distribution reference")
    psd_custom_points: Optional[str] = Field(None, description="Custom PSD points stored as JSON")
    
    # Complete PSD parameters (unified with cement model)
    psd_mode: Optional[str] = Field('log_normal', max_length=64, 
                                   description="PSD mode (rosin_rammler, log_normal, fuller, custom)")
    psd_d50: Optional[float] = Field(5.0, gt=0.0, description="PSD D50 parameter (μm)")
    psd_n: Optional[float] = Field(2.0, gt=0.0, description="PSD n parameter")
    psd_dmax: Optional[float] = Field(75.0, gt=0.0, description="PSD Dmax parameter (μm)")
    psd_median: Optional[float] = Field(5.0, gt=0.0, description="Median particle size (μm)")
    psd_spread: Optional[float] = Field(2.0, gt=0.0, description="PSD distribution spread parameter")
    psd_exponent: Optional[float] = Field(0.5, gt=0.0, description="PSD exponent parameter")
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Phase fractions
    aluminosilicate_glass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                           description="Aluminosilicate glass fraction")
    calcium_aluminum_disilicate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                                 description="Calcium aluminum disilicate fraction")
    tricalcium_aluminate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                          description="Tricalcium aluminate fraction")
    calcium_chloride_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                      description="Calcium chloride fraction")
    silica_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                           description="Silica fraction")
    anhydrate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                              description="Anhydrate fraction")
    
    # Chemical composition (oxide content) - typical Class F fly ash composition totaling 94%
    sio2_content: Optional[float] = Field(52.0, ge=0.0, le=100.0, description="SiO2 content percentage")
    al2o3_content: Optional[float] = Field(23.0, ge=0.0, le=100.0, description="Al2O3 content percentage")
    fe2o3_content: Optional[float] = Field(11.0, ge=0.0, le=100.0, description="Fe2O3 content percentage")
    cao_content: Optional[float] = Field(5.0, ge=0.0, le=100.0, description="CaO content percentage")
    mgo_content: Optional[float] = Field(2.0, ge=0.0, le=100.0, description="MgO content percentage")
    so3_content: Optional[float] = Field(1.0, ge=0.0, le=100.0, description="SO3 content percentage")
    
    # Physical properties
    loi: Optional[float] = Field(3.0, ge=0.0, le=20.0, description="Loss on ignition percentage")
    fineness_45um: Optional[float] = Field(20.0, ge=0.0, le=50.0, description="Fineness - percent retained on 45μm sieve")
    
    # Alkali characteristics
    na2o: Optional[float] = Field(1.2, ge=0.0, le=10.0, description="Na2O content percentage")
    k2o: Optional[float] = Field(2.1, ge=0.0, le=10.0, description="K2O content percentage")
    na2o_equivalent: Optional[float] = Field(None, ge=0.0, le=15.0, description="Na2O equivalent percentage")
    
    # Classification properties
    astm_class: Optional[str] = Field('class_f', description="ASTM classification")
    activity_index: Optional[float] = Field(85.0, ge=0.0, le=150.0, description="Activity index percentage")
    pozzolanic_activity: Optional[float] = Field(75.0, ge=0.0, le=150.0, description="Pozzolanic activity index percentage")
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(54000.0, gt=0.0, description="Activation energy (J/mol)")
    
    description: Optional[str] = Field(None, max_length=512, description="Fly ash description")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate fly ash name."""
        if not v or not v.strip():
            raise ValueError('Fly ash name cannot be empty')
        return v.strip()
    
    @field_validator('specific_gravity')
    @classmethod
    def validate_specific_gravity(cls, v):
        """Validate specific gravity."""
        if v is not None and v < 0:
            raise ValueError('Specific gravity cannot be negative')
        return v
    
    @model_validator(mode='after')
    def validate_phase_fractions_total(self):
        """Validate that phase fractions don't exceed 100%."""
        fractions = [
            self.aluminosilicate_glass_fraction,
            self.calcium_aluminum_disilicate_fraction,
            self.tricalcium_aluminate_fraction,
            self.calcium_chloride_fraction,
            self.silica_fraction,
            self.anhydrate_fraction
        ]
        
        valid_fractions = [f for f in fractions if f is not None]
        
        if len(valid_fractions) >= 3 and sum(valid_fractions) > 1.0:
            raise ValueError('Total phase fractions cannot exceed 1.0 (100%)')
        
        return self


class FlyAshUpdate(BaseModel):
    """Pydantic model for updating fly ash instances."""
    
    specific_gravity: Optional[float] = Field(None, ge=0.0, description="Specific gravity")
    psd: Optional[str] = Field(None, max_length=64, 
                              description="Particle size distribution reference")
    psd_custom_points: Optional[str] = Field(None, description="Custom PSD points stored as JSON")
    
    # Complete PSD parameters (unified with cement model)
    psd_mode: Optional[str] = Field(None, max_length=64, 
                                   description="PSD mode (rosin_rammler, log_normal, fuller, custom)")
    psd_d50: Optional[float] = Field(None, gt=0.0, description="PSD D50 parameter (μm)")
    psd_n: Optional[float] = Field(None, gt=0.0, description="PSD n parameter")
    psd_dmax: Optional[float] = Field(None, gt=0.0, description="PSD Dmax parameter (μm)")
    psd_median: Optional[float] = Field(None, gt=0.0, description="Median particle size (μm)")
    psd_spread: Optional[float] = Field(None, gt=0.0, description="PSD distribution spread parameter")
    psd_exponent: Optional[float] = Field(None, gt=0.0, description="PSD exponent parameter")
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Phase fractions
    aluminosilicate_glass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                           description="Aluminosilicate glass fraction")
    calcium_aluminum_disilicate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                                 description="Calcium aluminum disilicate fraction")
    tricalcium_aluminate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                          description="Tricalcium aluminate fraction")
    calcium_chloride_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                      description="Calcium chloride fraction")
    silica_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                           description="Silica fraction")
    anhydrate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                              description="Anhydrate fraction")
    
    # Chemical composition (oxide content)
    sio2_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="SiO2 content percentage")
    al2o3_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="Al2O3 content percentage")
    fe2o3_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="Fe2O3 content percentage")
    cao_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="CaO content percentage")
    mgo_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="MgO content percentage")
    so3_content: Optional[float] = Field(None, ge=0.0, le=100.0, description="SO3 content percentage")
    
    # Physical properties
    loi: Optional[float] = Field(None, ge=0.0, le=20.0, description="Loss on ignition percentage")
    fineness_45um: Optional[float] = Field(None, ge=0.0, le=50.0, description="Fineness - percent retained on 45μm sieve")
    
    # Alkali characteristics
    na2o: Optional[float] = Field(None, ge=0.0, le=10.0, description="Na2O content percentage")
    k2o: Optional[float] = Field(None, ge=0.0, le=10.0, description="K2O content percentage")
    na2o_equivalent: Optional[float] = Field(None, ge=0.0, le=15.0, description="Na2O equivalent percentage")
    
    # Classification properties
    astm_class: Optional[str] = Field(None, description="ASTM classification")
    activity_index: Optional[float] = Field(None, ge=0.0, le=150.0, description="Activity index percentage")
    pozzolanic_activity: Optional[float] = Field(None, ge=0.0, le=150.0, description="Pozzolanic activity index percentage")
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(None, gt=0.0, description="Activation energy (J/mol)")
    
    description: Optional[str] = Field(None, max_length=512, description="Fly ash description")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class FlyAshResponse(BaseModel):
    """Pydantic model for fly ash API responses."""
    
    name: str
    specific_gravity: Optional[float]
    psd: Optional[str]
    psd_mode: Optional[str]
    psd_d50: Optional[float]
    psd_n: Optional[float]
    psd_dmax: Optional[float]
    psd_median: Optional[float]
    psd_spread: Optional[float]
    psd_exponent: Optional[float]
    distribute_phases_by: Optional[int]
    aluminosilicate_glass_fraction: Optional[float]
    calcium_aluminum_disilicate_fraction: Optional[float]
    tricalcium_aluminate_fraction: Optional[float]
    calcium_chloride_fraction: Optional[float]
    silica_fraction: Optional[float]
    anhydrate_fraction: Optional[float]
    
    # Chemical composition
    sio2_content: Optional[float]
    al2o3_content: Optional[float]
    fe2o3_content: Optional[float]
    cao_content: Optional[float]
    mgo_content: Optional[float]
    so3_content: Optional[float]
    
    # Physical properties
    loi: Optional[float]
    fineness_45um: Optional[float]
    
    # Alkali characteristics
    na2o: Optional[float]
    k2o: Optional[float]
    na2o_equivalent: Optional[float]
    
    # Classification properties
    astm_class: Optional[str]
    activity_index: Optional[float]
    pozzolanic_activity: Optional[float]
    
    # Reaction parameters
    activation_energy: Optional[float]
    
    description: Optional[str]
    source: Optional[str]
    notes: Optional[str]
    total_phase_fraction: Optional[float]
    has_complete_phase_data: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True