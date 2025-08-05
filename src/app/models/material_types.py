#!/usr/bin/env python3
"""
Material Type Enumeration for VCCTL

Defines the types of materials that can be used in concrete mix designs.
This is a separate module to avoid circular imports between services and validation.
"""

from enum import Enum


class MaterialType(Enum):
    """Material type enumeration for mix design."""
    CEMENT = "cement"
    FLY_ASH = "fly_ash"
    SLAG = "slag"
    INERT_FILLER = "inert_filler"
    SILICA_FUME = "silica_fume"
    LIMESTONE = "limestone"
    AGGREGATE = "aggregate"