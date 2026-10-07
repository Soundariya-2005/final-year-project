"""
Privacy-Preserving REST API Endpoints.
Provides deterministic pseudonymization and controlled identity audit endpoints.
"""

from flask import Blueprint, jsonify, request
from privacy.pseudonymization import (
    pseudonymize_user_id,
    hash_original_id,
    identity_vault,
    apply_data_minimization,
)

privacy_bp = Blueprint("privacy", __name__, url_prefix="/api/privacy")

@privacy_bp.route("/status", methods=["GET"])
def privacy_status():
    """
    Returns the privacy subsystem status and data minimization parameters.
    Normal API responses never expose original employee identities.
    """
    public_users = identity_vault.get_public_registry()
    return jsonify({
        "status": "active",
        "mechanism": "Deterministic Pseudonymization & Data Minimization",
        "hash_algorithm": "SHA-256 (HMAC)",
        "pseudonym_format": "USR-[6-HEX]",
        "total_pseudonymized_users": len(public_users),
        "data_minimization_enforced": True,
        "controlled_lookup_enabled": True,
    }), 200


@privacy_bp.route("/pseudonymize", methods=["POST"])
def pseudonymize_endpoint():
    """
    POST /api/privacy/pseudonymize
    Accepts an original ID or list of IDs, generates deterministic pseudonyms,
    and registers them into the vault.
    
    IMPORTANT: Normal API response returns ONLY the pseudonymous ID and hash.
    The original ID is never returned in the normal response.
    """
    payload = request.get_json(silent=True) or {}
    original_id = payload.get("original_id")
    original_ids = payload.get("original_ids")

    if not original_id and not original_ids:
        return jsonify({
            "error": "Missing 'original_id' or 'original_ids' in request payload."
        }), 400

    if original_id:
        # Register single ID into the isolated vault
        reg_result = identity_vault.register_user(str(original_id))
        return jsonify({
            "status": "success",
            "pseudonymous_id": reg_result["pseudonymous_id"],
            "original_id_hash": reg_result["original_id_hash"],
            "created_at": reg_result["created_at"],
            "note": "Original identifier transformed and excluded from normal response."
        }), 200

    results = []
    for oid in original_ids:
        reg_result = identity_vault.register_user(str(oid))
        results.append({
            "pseudonymous_id": reg_result["pseudonymous_id"],
            "original_id_hash": reg_result["original_id_hash"],
        })

    return jsonify({
        "status": "success",
        "count": len(results),
        "pseudonymized_records": results,
    }), 200


@privacy_bp.route("/users", methods=["GET"])
def get_pseudonymized_users():
    """
    GET /api/privacy/users
    Returns all registered analytical entities.
    Strictly displays pseudonymous IDs and hashes; original IDs are withheld.
    """
    records = identity_vault.get_public_registry()
    return jsonify({
        "status": "ok",
        "total_users": len(records),
        "users": records,
    }), 200


@privacy_bp.route("/lookup", methods=["POST"])
def controlled_lookup_endpoint():
    """
    POST /api/privacy/lookup
    Controlled identity lookup mechanism for authorized compliance officers.
    Requires 'auth_token' in JSON payload or 'X-Audit-Token' header.
    Unauthenticated or unauthorized calls receive 403 Forbidden.
    """
    payload = request.get_json(silent=True) or {}
    pseudonymous_id = payload.get("pseudonymous_id")
    auth_token = payload.get("auth_token") or request.headers.get("X-Audit-Token")

    if not pseudonymous_id:
        return jsonify({"error": "Missing 'pseudonymous_id' parameter."}), 400

    try:
        audit_record = identity_vault.authorized_lookup(pseudonymous_id, auth_token)
        return jsonify({
            "status": "authorized",
            "message": "Authorized compliance identity lookup approved.",
            "record": audit_record,
        }), 200
    except PermissionError as pe:
        return jsonify({
            "status": "access_denied",
            "error": str(pe),
            "access_granted": False,
        }), 403
    except KeyError as ke:
        return jsonify({
            "status": "not_found",
            "error": str(ke),
            "access_granted": False,
        }), 404
