"""Central training pipelines for classical ML models."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np
import pandas as pd

from app.ai_ml.eligibility_model import EligibilityModel
from app.ai_ml.feature_engineering import FeatureEngineering
from app.ai_ml.lead_scoring_model import LeadScoringModel
from app.ai_ml.lender_ranking_model import LenderRankingModel
from app.ai_ml.model_registry import ModelRegistryService
from app.models.application import Application
from app.models.customer import Customer
from app.models.lead import Lead
from app.models.lender import Lender


# ==========================================
# SECTION: Training Logic
# ==========================================
def train_lead_model(tenant_id: int) -> dict[str, Any]:
    """Train lead scoring model end-to-end.

    Workflow:
    1) fetch historical data
    2) clean dataset
    3) encode categorical values (inside model pipeline)
    4) split train/test
    5) train
    6) evaluate
    7) save model
    8) register version
    """
    raw_df = _fetch_lead_training_data(tenant_id)
    if len(raw_df) < 30:
        raw_df = pd.concat([raw_df, _bootstrap_lead_data(120)], ignore_index=True)

    X = FeatureEngineering.prepare_lead_features(raw_df)
    y = raw_df["label"].astype(int)

    version = ModelRegistryService.next_version(model_name="lead_scoring", tenant_id=tenant_id)
    model = LeadScoringModel(model_version=version)
    metrics = model.train(X, y)

    artifact_path = ModelRegistryService.build_artifact_path(
        model_name="lead_scoring",
        tenant_id=tenant_id,
        version=version,
    )
    model.save_model(artifact_path)

    entry = ModelRegistryService.register_model(
        tenant_id=tenant_id,
        model_name="lead_scoring",
        file_path=artifact_path,
        accuracy=metrics.accuracy,
        precision=metrics.precision,
        recall=metrics.recall,
        version=version,
    )

    return {
        "model": "lead_scoring",
        "version": version,
        "metrics": asdict(metrics),
        "registry_id": entry.id,
        "artifact": artifact_path,
    }


def train_eligibility_model(tenant_id: int) -> dict[str, Any]:
    """Train eligibility approval model end-to-end."""
    raw_df = _fetch_eligibility_training_data(tenant_id)
    if len(raw_df) < 30:
        raw_df = pd.concat([raw_df, _bootstrap_eligibility_data(120)], ignore_index=True)

    X = FeatureEngineering.prepare_eligibility_features(raw_df)
    y = raw_df["label"].astype(int)

    version = ModelRegistryService.next_version(model_name="eligibility", tenant_id=tenant_id)
    model = EligibilityModel(model_version=version)
    metrics = model.train(X, y)

    artifact_path = ModelRegistryService.build_artifact_path(
        model_name="eligibility",
        tenant_id=tenant_id,
        version=version,
    )
    model.save_model(artifact_path)

    entry = ModelRegistryService.register_model(
        tenant_id=tenant_id,
        model_name="eligibility",
        file_path=artifact_path,
        accuracy=metrics.accuracy,
        precision=metrics.precision,
        recall=metrics.recall,
        version=version,
    )

    return {
        "model": "eligibility",
        "version": version,
        "metrics": asdict(metrics),
        "registry_id": entry.id,
        "artifact": artifact_path,
    }


def train_lender_model(tenant_id: int) -> dict[str, Any]:
    """Train lender ranking calibration model end-to-end."""
    raw_df = _fetch_lender_training_data(tenant_id)
    if len(raw_df) < 30:
        raw_df = pd.concat([raw_df, _bootstrap_lender_data(80)], ignore_index=True)

    X = FeatureEngineering.prepare_lender_features(raw_df)
    y = pd.to_numeric(raw_df["target_score"], errors="coerce").fillna(50.0)

    version = ModelRegistryService.next_version(model_name="lender_ranking", tenant_id=tenant_id)
    model = LenderRankingModel(model_version=version)
    metrics = model.train(X, y)

    artifact_path = ModelRegistryService.build_artifact_path(
        model_name="lender_ranking",
        tenant_id=tenant_id,
        version=version,
    )
    model.save_model(artifact_path)

    entry = ModelRegistryService.register_model(
        tenant_id=tenant_id,
        model_name="lender_ranking",
        file_path=artifact_path,
        accuracy=max(0.0, 1.0 - min(metrics.mae / 100.0, 1.0)),
        precision=None,
        recall=None,
        version=version,
    )

    return {
        "model": "lender_ranking",
        "version": version,
        "metrics": asdict(metrics),
        "registry_id": entry.id,
        "artifact": artifact_path,
    }


# ==========================================
# SECTION: Prediction Logic
# ==========================================
def _fetch_lead_training_data(tenant_id: int) -> pd.DataFrame:
    """Prepare historical lead dataset with DISBURSED vs LOST labels."""
    rows: list[dict[str, Any]] = []
    leads = Lead.query.filter(
        Lead.tenant_id == tenant_id,
        Lead.is_deleted.is_(False),
        Lead.stage.in_(["DISBURSED", "LOST"]),
    ).all()

    for lead in leads:
        loan_amount = float(lead.loan_amount or 0)
        rows.append(
            {
                "lead_source": lead.source or "unknown",
                "loan_type": lead.loan_type or "unknown",
                "city_tier": "tier_1" if str(lead.mobile).startswith(("9", "8")) else "tier_2",
                "income_band": _income_band_from_loan(loan_amount),
                "credit_score": float(lead.ai_score_placeholder or 65) * 10,
                "response_time": 25.0,
                "followup_count": 3.0,
                "document_upload_speed": 48.0,
                "campaign_source": lead.source or "organic",
                "agent_history": 0.6,
                "time_to_first_contact": 20.0,
                "label": 1 if lead.stage == "DISBURSED" else 0,
            }
        )

    return pd.DataFrame(rows)


def _fetch_eligibility_training_data(tenant_id: int) -> pd.DataFrame:
    """Build eligibility training dataset from applications + customer info."""
    rows: list[dict[str, Any]] = []

    applications = Application.query.filter_by(tenant_id=tenant_id, is_deleted=False).all()
    for app in applications:
        customer = Customer.query.filter_by(
            id=app.customer_id,
            tenant_id=tenant_id,
            is_deleted=False,
        ).first()
        if not customer:
            continue

        monthly_income = float(customer.monthly_income or 0)
        existing_emis = float(customer.existing_emis or 0)
        foir = (existing_emis / monthly_income * 100) if monthly_income > 0 else 100
        dti = foir
        ltv = min((float(app.loan_amount or 0) / max(float(app.loan_amount or 1), 1)) * 100, 100)

        label = 1 if app.current_stage in {"SANCTIONED", "DISBURSED"} or app.status in {"approved", "sanctioned"} else 0

        rows.append(
            {
                "credit_score": float(customer.risk_score_placeholder or 70) * 10,
                "monthly_income": monthly_income,
                "foir": foir,
                "dti": dti,
                "ltv": ltv,
                "employment_type": customer.occupation or "salaried",
                "loan_amount": float(app.loan_amount or 0),
                "loan_type": app.loan_type or "unknown",
                "city_tier": "tier_1" if str(customer.mobile).startswith(("9", "8")) else "tier_2",
                "existing_emis": existing_emis,
                "label": label,
            }
        )

    return pd.DataFrame(rows)


def _fetch_lender_training_data(tenant_id: int) -> pd.DataFrame:
    """Build lender ranking dataset from historical lender metrics."""
    rows: list[dict[str, Any]] = []
    lenders = Lender.query.filter_by(tenant_id=tenant_id, is_deleted=False).all()

    for lender in lenders:
        approval = float(lender.approval_percentage or 50)
        interest = float(lender.interest_rate or 12.0)
        days = float(lender.speed_score or 5.0)
        doc_ease = float(lender.ease_score or 50)
        hist = float(lender.approval_percentage or 50)

        # Historical pseudo target score used to train ML correction model.
        rate_competitiveness = max(0.0, min(100.0, 100.0 - (interest * 6)))
        speed_score = max(0.0, min(100.0, 100.0 - (days * 10)))
        target = 0.4 * approval + 0.2 * rate_competitiveness + 0.2 * speed_score + 0.2 * doc_ease

        rows.append(
            {
                "bank_name": lender.lender_name,
                "approval_probability": approval,
                "interest_rate": interest,
                "avg_disbursal_days": days,
                "documentation_ease": doc_ease,
                "historical_approval_rate": hist,
                "target_score": target,
            }
        )

    return pd.DataFrame(rows)


def _bootstrap_lead_data(size: int) -> pd.DataFrame:
    """Generate fallback lead data for cold-start training."""
    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        {
            "lead_source": rng.choice(["meta_ads", "google_ads", "organic", "referral"], size=size),
            "loan_type": rng.choice(["home", "personal", "business"], size=size),
            "city_tier": rng.choice(["tier_1", "tier_2", "tier_3"], size=size),
            "income_band": rng.choice(["low", "mid", "high"], size=size),
            "credit_score": rng.normal(700, 60, size=size).clip(500, 850),
            "response_time": rng.integers(5, 120, size=size),
            "followup_count": rng.integers(0, 8, size=size),
            "document_upload_speed": rng.integers(2, 120, size=size),
            "campaign_source": rng.choice(["meta", "search", "affiliate"], size=size),
            "agent_history": rng.uniform(0.2, 0.9, size=size),
            "time_to_first_contact": rng.integers(1, 180, size=size),
        }
    )
    # Deterministic pseudo-label using rule score.
    signal = (
        (df["credit_score"] / 850) * 0.35
        + (1 - (df["response_time"] / 120)).clip(0, 1) * 0.25
        + (df["agent_history"] * 0.25)
        + (df["followup_count"].clip(0, 5) / 5) * 0.15
    )
    df["label"] = (signal > 0.55).astype(int)
    return df


def _bootstrap_eligibility_data(size: int) -> pd.DataFrame:
    """Generate fallback eligibility data for cold-start training."""
    rng = np.random.default_rng(7)
    df = pd.DataFrame(
        {
            "credit_score": rng.normal(705, 55, size=size).clip(500, 850),
            "monthly_income": rng.integers(25000, 180000, size=size),
            "foir": rng.uniform(15, 75, size=size),
            "dti": rng.uniform(15, 70, size=size),
            "ltv": rng.uniform(40, 95, size=size),
            "employment_type": rng.choice(["salaried", "self_employed"], size=size),
            "loan_amount": rng.integers(200000, 5000000, size=size),
            "loan_type": rng.choice(["home", "lap", "personal"], size=size),
            "city_tier": rng.choice(["tier_1", "tier_2", "tier_3"], size=size),
            "existing_emis": rng.integers(2000, 60000, size=size),
        }
    )
    score = (
        (df["credit_score"] / 850) * 0.35
        + ((100 - df["foir"]) / 100) * 0.30
        + ((100 - df["dti"]) / 100) * 0.20
        + ((100 - df["ltv"]) / 100) * 0.15
    )
    df["label"] = (score > 0.58).astype(int)
    return df


def _bootstrap_lender_data(size: int) -> pd.DataFrame:
    """Generate fallback lender performance data for cold-start training."""
    rng = np.random.default_rng(11)
    df = pd.DataFrame(
        {
            "bank_name": [f"Bank_{i+1}" for i in range(size)],
            "approval_probability": rng.uniform(45, 95, size=size),
            "interest_rate": rng.uniform(8.5, 15.5, size=size),
            "avg_disbursal_days": rng.uniform(2, 15, size=size),
            "documentation_ease": rng.uniform(35, 95, size=size),
            "historical_approval_rate": rng.uniform(40, 90, size=size),
        }
    )

    max_rate = max(float(df["interest_rate"].max()), 0.0001)
    min_rate = float(df["interest_rate"].min())
    rate_score = 100.0 if max_rate == min_rate else 100.0 * (max_rate - df["interest_rate"]) / (max_rate - min_rate)

    max_days = max(float(df["avg_disbursal_days"].max()), 0.0001)
    min_days = float(df["avg_disbursal_days"].min())
    speed_score = 100.0 if max_days == min_days else 100.0 * (max_days - df["avg_disbursal_days"]) / (max_days - min_days)

    df["target_score"] = (
        0.4 * df["approval_probability"]
        + 0.2 * rate_score
        + 0.2 * speed_score
        + 0.2 * df["documentation_ease"]
    )
    return df


def _income_band_from_loan(loan_amount: float) -> str:
    """Simple helper to infer income band from loan amount proxy."""
    if loan_amount >= 2_000_000:
        return "high"
    if loan_amount >= 700_000:
        return "mid"
    return "low"


# ==========================================
# SECTION: Serialization
# ==========================================
# Model serialization is handled by each model class save_model method,
# while registry persistence is handled via ModelRegistryService.
