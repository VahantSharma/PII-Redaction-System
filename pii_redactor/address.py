"""
Physical address detector — re-export shim.

This module now lives in detectors/address.py.
This file exists so that any old `from pii_redactor.address import ...`
continues to work.
"""

from pii_redactor.detectors.address import (  # noqa: F401
    detect_addresses_in_text,
    extract_components,
    AddressComponents,
)

__all__ = [
    "detect_addresses_in_text",
    "extract_components",
    "AddressComponents",
]
