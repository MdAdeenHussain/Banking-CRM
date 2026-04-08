"""Identity graph service for reuse and cluster detection."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import json
from collections import Counter, defaultdict, deque
from typing import Any

from app.models.audit_log import AuditLog
from app.models.customer import Customer


# ==========================================
# SECTION: Fraud Detection
# ==========================================
class IdentityGraphService:
    """Build simple identity graphs and find suspicious clusters."""

    def __init__(self, tenant_id: int) -> None:
        self.tenant_id = tenant_id

    def build_identity_graph(self) -> dict[str, Any]:
        """Build identity graph from customer identities and device logs."""
        adjacency: dict[str, set[str]] = defaultdict(set)
        node_metadata: dict[str, dict[str, Any]] = {}

        customers = Customer.query.filter_by(tenant_id=self.tenant_id, is_deleted=False).all()
        for customer in customers:
            customer_node = f"customer:{customer.id}"
            node_metadata[customer_node] = {
                "type": "customer",
                "label": customer.full_name,
            }

            identity_pairs = {
                "pan": customer.pan,
                "mobile": customer.mobile,
                "email": customer.email,
                "aadhaar": customer.aadhaar,
            }
            for identity_type, identity_value in identity_pairs.items():
                if not identity_value:
                    continue
                identity_node = f"{identity_type}:{str(identity_value).strip().lower()}"
                adjacency[customer_node].add(identity_node)
                adjacency[identity_node].add(customer_node)
                node_metadata[identity_node] = {
                    "type": identity_type,
                    "label": str(identity_value),
                }

        device_logs = AuditLog.query.filter_by(
            tenant_id=self.tenant_id,
            action="device_fingerprint_seen",
            is_deleted=False,
        ).all()
        for audit_log in device_logs:
            details = self._parse_log(audit_log.details)
            fingerprint = details.get("fingerprint")
            if not fingerprint:
                continue
            device_node = f"device:{fingerprint}"
            node_metadata[device_node] = {"type": "device", "label": fingerprint[:12]}

            ip_address = str(details.get("ip", "")).strip()
            if ip_address:
                ip_node = f"ip:{ip_address}"
                adjacency[device_node].add(ip_node)
                adjacency[ip_node].add(device_node)
                node_metadata[ip_node] = {"type": "ip", "label": ip_address}

            identifiers = details.get("identifiers", {})
            for identity_type in ["pan", "mobile", "email", "aadhaar"]:
                identity_value = str(identifiers.get(identity_type, "")).strip().lower()
                if not identity_value:
                    continue
                identity_node = f"{identity_type}:{identity_value}"
                adjacency[device_node].add(identity_node)
                adjacency[identity_node].add(device_node)
                node_metadata.setdefault(
                    identity_node,
                    {"type": identity_type, "label": identity_value},
                )

        edges = []
        for source, targets in adjacency.items():
            for target in targets:
                if source < target:
                    edges.append({"source": source, "target": target})

        return {
            "nodes": [{"id": node_id, **metadata} for node_id, metadata in node_metadata.items()],
            "edges": edges,
            "adjacency": adjacency,
        }

    def find_suspicious_clusters(self) -> list[dict[str, Any]]:
        """Find identity clusters with unusual shared usage."""
        graph = self.build_identity_graph()
        adjacency = graph["adjacency"]
        visited: set[str] = set()
        suspicious_clusters: list[dict[str, Any]] = []

        for start_node in adjacency.keys():
            if start_node in visited:
                continue

            queue = deque([start_node])
            cluster_nodes: set[str] = set()
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                cluster_nodes.add(node)
                for neighbour in adjacency.get(node, set()):
                    if neighbour not in visited:
                        queue.append(neighbour)

            if not cluster_nodes:
                continue

            type_counter = Counter(node.split(":", 1)[0] for node in cluster_nodes)
            reasons = []
            if type_counter.get("pan", 0) > 1:
                reasons.append("Multiple PAN identities linked in one cluster.")
            if type_counter.get("mobile", 0) > 1:
                reasons.append("Multiple mobiles linked through shared identity paths.")
            if type_counter.get("device", 0) > 0 and type_counter.get("pan", 0) > 1:
                reasons.append("Shared device linked across multiple PAN identities.")
            if type_counter.get("ip", 0) > 0 and type_counter.get("pan", 0) > 1:
                reasons.append("Same IP linked to multiple PAN identities.")

            if reasons:
                suspicious_clusters.append(
                    {
                        "nodes": sorted(cluster_nodes),
                        "summary": type_counter,
                        "risk_level": "HIGH" if type_counter.get("pan", 0) > 1 else "MEDIUM",
                        "reasons": reasons,
                    }
                )

        return suspicious_clusters

    def score_identity_risk(
        self,
        *,
        customer: Customer | None = None,
        identifiers: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Score identity reuse risk from customer duplicates and clusters."""
        duplicate_count = 0
        reasons = []
        identifiers = identifiers or {}

        if customer and customer.pan:
            pan_count = Customer.query.filter_by(
                tenant_id=self.tenant_id,
                pan=customer.pan,
                is_deleted=False,
            ).count()
            if pan_count > 1:
                duplicate_count += pan_count - 1
                reasons.append(f"PAN reused across {pan_count} customer profiles.")

        for field_name in ["pan", "mobile", "email", "aadhaar"]:
            value = str(identifiers.get(field_name, "")).strip()
            if not value:
                continue
            count = Customer.query.filter_by(
                tenant_id=self.tenant_id,
                **{field_name: value},
                is_deleted=False,
            ).count()
            if count > 1:
                duplicate_count += count - 1
                reasons.append(f"{field_name.upper()} reused across {count} customer profiles.")

        suspicious_clusters = self.find_suspicious_clusters()
        cluster_hits = [
            cluster for cluster in suspicious_clusters
            if any(
                str(identifiers.get(field_name, "")).strip().lower()
                and f"{field_name}:{str(identifiers.get(field_name, '')).strip().lower()}" in cluster["nodes"]
                for field_name in ["pan", "mobile", "email", "aadhaar"]
            )
        ]
        if cluster_hits:
            duplicate_count += len(cluster_hits)
            reasons.extend(cluster["reasons"][0] for cluster in cluster_hits if cluster["reasons"])

        score = min(100, duplicate_count * 20)
        return {
            "identity_score": int(score),
            "risk_level": "HIGH" if score > 70 else "MEDIUM" if score >= 40 else "LOW",
            "reasons": reasons,
            "suspicious_clusters": cluster_hits,
        }

    def _parse_log(self, details: str | None) -> dict[str, Any]:
        """Parse JSON log payloads safely."""
        try:
            return json.loads(details or "{}")
        except json.JSONDecodeError:
            return {}


# ==========================================
# SECTION: Anomaly Scoring
# ==========================================
# Cluster and duplicate counts become features for anomaly scoring.


# ==========================================
# SECTION: Forensics
# ==========================================
# Identity graphs support forensic investigation but do not inspect files.


# ==========================================
# SECTION: Alerts
# ==========================================
# Suspicious clusters can be escalated through alert_service.py.
