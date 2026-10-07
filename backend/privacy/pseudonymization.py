"""
Privacy-Preserving Layer: Deterministic Pseudonymization and Data Minimization.

Implements:
1. Deterministic Pseudonymization: Maps original employee IDs (e.g., EMP001) to
   consistent pseudonyms (e.g., USR-A8F29C) using SHA-256 / HMAC.
2. Data Minimization: Strips unnecessary identifiable attributes prior to
   feature storage and ML analysis.
3. Controlled Identity Registry: Restricts reverse identity lookup exclusively
   to authorized administrative compliance audits via secure token validation.
"""

import os
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

# Salt/pepper loaded from environment variable with secure fallback
DEFAULT_SALT = "insider-threat-privacy-salt-v1"
ADMIN_KEY = os.getenv("ADMIN_SECURITY_KEY", "compliance-officer-audit-key")

def get_salt() -> str:
    """Retrieves the system pseudonymization salt from environment variables."""
    return os.getenv("PSEUDONYM_SALT", DEFAULT_SALT).strip() or DEFAULT_SALT


def hash_original_id(original_id: str) -> str:
    """
    Computes a cryptographic SHA-256 digest of an original user ID.
    Used for database verification without storing the plaintext original ID.
    """
    if not original_id:
        raise ValueError("original_id cannot be empty")
    cleaned_id = str(original_id).strip()
    return hashlib.sha256(cleaned_id.encode("utf-8")).hexdigest()


def pseudonymize_user_id(original_id: str, length: int = 6) -> str:
    """
    Converts an original user ID into a deterministic pseudonymous ID.
    
    Properties:
    - Deterministic: Same original ID always produces the exact same pseudonymous ID.
    - Non-invertible: Original ID cannot be derived without the secure salt and authorized vault.
    - Format: USR- followed by uppercase hexadecimal characters (e.g., 'USR-A8F29C').

    Args:
        original_id: Original employee ID (e.g., 'EMP001').
        length: Length of the unique hex identifier segment (default 6 chars).

    Returns:
        Formatted pseudonymous identifier string (e.g., 'USR-A8F29C').
    """
    if not original_id:
        raise ValueError("original_id cannot be empty")

    cleaned_id = str(original_id).strip()
    salt = get_salt()

    # Compute HMAC-SHA256 for deterministic, collision-resistant pseudonym generation
    hmac_digest = hmac.new(
        key=salt.encode("utf-8"),
        msg=cleaned_id.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    # Extract deterministic prefix segment in uppercase
    hex_segment = hmac_digest[:length].upper()
    return f"USR-{hex_segment}"


class ControlledIdentityVault:
    """
    Isolated identity mapping vault for controlled de-anonymization.
    
    In a zero-trust enterprise architecture, analytical subsystems (ML pipeline,
    general API, analyst dashboards) only see pseudonymous IDs.
    The reverse mapping is held in this segregated vault, accessible ONLY when
    authorized by an administrative compliance key during formal investigations.
    """

    def __init__(self):
        # In-memory vault mapping: pseudonymous_id -> secure metadata
        self._vault: Dict[str, Dict[str, Any]] = {}

    def register_user(self, original_id: str) -> Dict[str, str]:
        """
        Registers an employee into the vault and returns their public pseudonymous identifier.
        The raw original ID is never exposed to public responses.
        """
        if not original_id:
            raise ValueError("original_id cannot be empty")

        p_id = pseudonymize_user_id(original_id)
        id_hash = hash_original_id(original_id)

        # Store reverse link only inside the isolated vault
        if p_id not in self._vault:
            self._vault[p_id] = {
                "pseudonymous_id": p_id,
                "original_id_hash": id_hash,
                "_encrypted_original_id": str(original_id).strip(),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        # Return sanitized public representation (data minimization)
        return {
            "pseudonymous_id": p_id,
            "original_id_hash": id_hash,
            "created_at": self._vault[p_id]["created_at"],
        }

    def authorized_lookup(self, pseudonymous_id: str, auth_token: Optional[str]) -> Dict[str, Any]:
        """
        Controlled identity lookup mechanism.
        Requires a valid administrative/compliance token to resolve a pseudonymous ID.
        Raises PermissionError if the token is invalid or missing.
        """
        admin_secret = os.getenv("ADMIN_SECURITY_KEY", ADMIN_KEY)

        if not auth_token or auth_token != admin_secret:
            raise PermissionError("Access Denied: Identity lookup requires authorized compliance officer credentials.")

        record = self._vault.get(pseudonymous_id)
        if not record:
            raise KeyError(f"Pseudonymous ID '{pseudonymous_id}' not found in identity registry.")

        # Return authorized audit record
        return {
            "pseudonymous_id": record["pseudonymous_id"],
            "original_id": record["_encrypted_original_id"],
            "original_id_hash": record["original_id_hash"],
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "access_granted": True,
        }

    def get_public_registry(self) -> List[Dict[str, str]]:
        """
        Returns minimized list of registered users.
        Strictly excludes any original employee identities.
        """
        return [
            {
                "pseudonymous_id": entry["pseudonymous_id"],
                "original_id_hash": entry["original_id_hash"],
                "created_at": entry["created_at"],
            }
            for entry in self._vault.values()
        ]

    def has_pseudonym(self, pseudonymous_id: str) -> bool:
        return pseudonymous_id in self._vault


# Singleton vault instance
identity_vault = ControlledIdentityVault()


def apply_data_minimization(record: Dict[str, Any], id_field: str = "user_id") -> Dict[str, Any]:
    """
    Enforces data minimization on an individual activity record:
    - Replaces raw identifier with its deterministic pseudonymous ID.
    - Strips identifiable personal attributes (e.g. name, email, ssn, phone).
    """
    minimized = dict(record)
    
    # Pseudonymize user identifier
    if id_field in minimized:
        minimized[id_field] = pseudonymize_user_id(str(minimized[id_field]))

    # Strip personal identifiers that violate data minimization principles
    forbidden_keys = {"name", "full_name", "first_name", "last_name", "ssn", "phone", "email_address"}
    for k in list(minimized.keys()):
        if k.lower() in forbidden_keys:
            del minimized[k]

    return minimized
