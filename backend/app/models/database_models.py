"""Database ORM Models Module.

Defines the core persistence schema for dataset metadata, prediction runs,
business performance scores, and system audit logs.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, Boolean
from app.core.database import Base


class DatasetMetadata(Base):
    """Metadata tracking for ingested ERP/CRM raw and preprocessed datasets."""

    __tablename__ = "datasets_metadata"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    domain = Column(String(50), nullable=False, index=True)  # sales, inventory, finance, hr, procurement
    file_path = Column(String(512), nullable=False)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    schema_info = Column(JSON, nullable=True)  # Inferred column types and mappings
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PredictionRecord(Base):
    """Stores hybrid ensemble predictions across business domains."""

    __tablename__ = "predictions_records"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(50), nullable=False, index=True)
    target_metric = Column(String(100), nullable=False)
    predicted_value = Column(Float, nullable=False)
    model_weights = Column(JSON, nullable=True)  # {w_RF, w_XGB, w_ANN}
    raw_predictions = Column(JSON, nullable=True)  # {RF, XGB, ANN}
    prediction_timestamp = Column(DateTime, default=datetime.utcnow)


class BusinessScoreRecord(Base):
    """Stores calculated domain scores (S, I, F, E) and overall Bp score."""

    __tablename__ = "business_score_records"

    id = Column(Integer, primary_key=True, index=True)
    sales_score = Column(Float, nullable=True)      # S
    inventory_score = Column(Float, nullable=True)  # I
    finance_score = Column(Float, nullable=True)    # F
    employee_score = Column(Float, nullable=True)   # E
    bp_score = Column(Float, nullable=True)         # Bp = (S + I + F + E) / 4
    score_metadata = Column(JSON, nullable=True)    # Detailed metric breakdowns
    calculated_at = Column(DateTime, default=datetime.utcnow)


class ExplanationLog(Base):
    """Stores SHAP analysis metadata and LLaMA-generated natural language summaries."""

    __tablename__ = "explanation_logs"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(50), nullable=False, index=True)
    prediction_id = Column(Integer, nullable=True)
    shap_summary = Column(JSON, nullable=True)
    natural_language_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
