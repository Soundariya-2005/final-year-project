"""
Privacy-Preserving Module.
Exports deterministic pseudonymization and data minimization utilities.
"""

from .pseudonymization import (
    pseudonymize_user_id,
    hash_original_id,
    identity_vault,
    ControlledIdentityVault,
    apply_data_minimization,
)

__all__ = [
    "pseudonymize_user_id",
    "hash_original_id",
    "identity_vault",
    "ControlledIdentityVault",
    "apply_data_minimization",
]
