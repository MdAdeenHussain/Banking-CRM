"""Device fingerprinting and reuse detection service."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any

from app.extensions import db
from app.models.audit_log import AuditLog


# ==========================================
# SECTION: Fraud Detection
# ==========================================
class DeviceFingerprintService:
    """Track device reuse and device-linked identity anomalies."""

    def __init__(self, tenant_id: int, actor_user_id: int | None = None) -> None:
        self.tenant_id = tenant_id
        self.actor_user_id = actor_user_id

    def generate_device_fingerprint(self, payload: dict[str, Any]) -> str:
        """Generate stable device fingerprint from request/device traits."""
        fingerprint_parts = [
            payload.get("device_id", ""),
            payload.get("browser_fingerprint", ""),
            payload.get("os_fingerprint", ""),
            payload.get("ip", ""),
            payload.get("user_agent", ""),
        ]
        raw_value = "|".join(str(part).strip().lower() for part in fingerprint_parts)
        return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()

    def register_device_observation(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist device observation into audit logs for reuse analysis."""
        fingerprint = self.generate_device_fingerprint(payload)
        details = {
            "fingerprint": fingerprint,
            "device_id": payload.get("device_id"),
            "browser_fingerprint": payload.get("browser_fingerprint"),
            "os_fingerprint": payload.get("os_fingerprint"),
            "ip": payload.get("ip"),
            "user_agent": payload.get("user_agent"),
            "identifiers": payload.get("identifiers", {}),
        }

        audit_log = AuditLog(
            tenant_id=self.tenant_id,
            user_id=self.actor_user_id,
            action="device_fingerprint_seen",
            entity="device",
            entity_id=fingerprint,
            details=json.dumps(details, ensure_ascii=True),
            ip_address=str(payload.get("ip", "")) or None,
        )
        db.session.add(audit_log)
        db.session.commit()

        return {"fingerprint": fingerprint, "details": details}

    def detect_multiple_identities(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Detect multiple identities tied to the same device."""
        fingerprint = self.generate_device_fingerprint(payload)
        observations = self._load_observations_for_fingerprint(fingerprint)
        observations.append(
            {
                "fingerprint": fingerprint,
                "identifiers": payload.get("identifiers", {}),
                "ip": payload.get("ip"),
            }
        )

        identity_sets = defaultdict(set)
        for observation in observations:
            identifiers = observation.get("identifiers", {})
            for key in ["pan", "aadhaar", "mobile", "email"]:
                value = str(identifiers.get(key, "")).strip().lower()
                if value:
                    identity_sets[key].add(value)

        max_identity_count = max((len(values) for values in identity_sets.values()), default=1)
        score = min(100, max(0, (max_identity_count - 1) * 25))
        reasons = [
            f"Same device reused across {len(values)} unique {key.upper()} values."
            for key, values in identity_sets.items()
            if len(values) > 1
        ]

        return {
            "fingerprint": fingerprint,
            "identity_sets": {key: sorted(values) for key, values in identity_sets.items()},
            "score": score,
            "risk_level": self._risk_level(score),
            "reasons": reasons,
        }

    def detect_device_reuse(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Detect overall device/IP reuse and return device risk score."""
        fingerprint = self.generate_device_fingerprint(payload)
        observations = self._load_observations_for_fingerprint(fingerprint)
        usage_count = len(observations) + 1
        ip_matches = self._load_observations_for_ip(str(payload.get("ip", "")))
        multiple_identity_result = self.detect_multiple_identities(payload)

        score = min(
            100,
            ((usage_count - 1) * 12)
            + ((len(ip_matches) - 1) * 8)
            + int(multiple_identity_result["score"] * 0.5),
        )

        return {
            "fingerprint": fingerprint,
            "usage_count": usage_count,
            "ip_reuse_count": len(ip_matches),
            "score": int(score),
            "risk_level": self._risk_level(int(score)),
            "multiple_identity_result": multiple_identity_result,
        }

    def analyze_device(self, payload: dict[str, Any], *, persist: bool = True) -> dict[str, Any]:
        """Complete device-risk analysis entry point."""
        if persist:
            registration = self.register_device_observation(payload)
        else:
            registration = {
                "fingerprint": self.generate_device_fingerprint(payload),
                "details": payload,
            }
        reuse_result = self.detect_device_reuse(payload)
        return {
            "fingerprint": registration["fingerprint"],
            "device_score": reuse_result["score"],
            "risk_level": reuse_result["risk_level"],
            "usage_count": reuse_result["usage_count"],
            "ip_reuse_count": reuse_result["ip_reuse_count"],
            "multiple_identity_result": reuse_result["multiple_identity_result"],
        }

    def _load_observations_for_fingerprint(self, fingerprint: str) -> list[dict[str, Any]]:
        """Load prior device observations for one fingerprint."""
        logs = AuditLog.query.filter_by(
            tenant_id=self.tenant_id,
            action="device_fingerprint_seen",
            entity_id=fingerprint,
            is_deleted=False,
        ).all()
        return [self._parse_log(log) for log in logs]

    def _load_observations_for_ip(self, ip_address: str) -> list[dict[str, Any]]:
        """Load prior device observations for one IP address."""
        if not ip_address:
            return []
        logs = AuditLog.query.filter_by(
            tenant_id=self.tenant_id,
            action="device_fingerprint_seen",
            ip_address=ip_address,
            is_deleted=False,
        ).all()
        return [self._parse_log(log) for log in logs]

    def _parse_log(self, audit_log: AuditLog) -> dict[str, Any]:
        """Parse JSON details from audit log safely."""
        try:
            return json.loads(audit_log.details or "{}")
        except json.JSONDecodeError:
            return {}

    def _risk_level(self, score: int) -> str:
        """Map score to LOW/MEDIUM/HIGH."""
        if score > 70:
            return "HIGH"
        if score >= 40:
            return "MEDIUM"
        return "LOW"


# ==========================================
# SECTION: Anomaly Scoring
# ==========================================
# Device/IP reuse counts are later transformed into anomaly features.


# ==========================================
# SECTION: Forensics
# ==========================================
# Device signals complement document forensics but do not inspect files.


# ==========================================
# SECTION: Alerts
# ==========================================
# High-risk device findings can be promoted to notifications.
