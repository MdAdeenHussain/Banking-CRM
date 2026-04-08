"""Document intelligence package exports."""

# ==========================================
# SECTION: Imports
# ==========================================
from app.documents.routes import documents_bp


# ==========================================
# SECTION: Core Logic
# ==========================================
__all__ = ["documents_bp"]


# ==========================================
# SECTION: Validation
# ==========================================
# Validation helpers are provided in app.documents.validators


# ==========================================
# SECTION: Fraud Checks
# ==========================================
# Fraud logic is provided in app.documents.fraud_engine
