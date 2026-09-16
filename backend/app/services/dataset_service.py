"""Dataset Management Service.

Coordinates data ingestion, semantic schema interpretation (LLaMA Copilot),
and deterministic cleaning workflows.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from app.data.ingestion.connectors import CSVConnector, IngestionResult
from app.data.preprocessing.cleaner import DeterministicDataCleaner, CleaningReport
from app.llm.llama_client import LocalLLaMAClient
from app.llm.semantic_copilot import SemanticCopilot, SchemaInferenceResult
from app.models.database_models import DatasetMetadata
from app.core.logging_config import logger


class DatasetService:
    """Service boundary for dataset ingestion and preprocessing workflows."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db
        self.csv_connector = CSVConnector()
        self.cleaner = DeterministicDataCleaner()
        self.llm_client = LocalLLaMAClient()
        self.copilot = SemanticCopilot(self.llm_client)

    async def ingest_and_analyze(
        self,
        file_path: str,
        domain: str,
        filename: str,
    ) -> Dict[str, Any]:
        """Ingests raw file, runs semantic copilot schema analysis, and deterministic cleaning."""
        # 1. Ingestion
        ingest_res = self.csv_connector.ingest(file_path, domain=domain)

        # 2. Semantic Copilot Analysis
        sample_rows = ingest_res.dataframe.head(3).to_dict(orient="records")
        columns = list(ingest_res.dataframe.columns)
        schema_inference = await self.copilot.infer_schema(
            domain=domain,
            columns=columns,
            sample_rows=sample_rows,
        )

        # 3. Deterministic Cleaning
        cleaned_df, cleaning_report = self.cleaner.clean(
            df=ingest_res.dataframe,
            schema_mapping=schema_inference.column_mappings,
        )

        # 4. Optional Database Tracking
        dataset_id = None
        if self.db:
            try:
                record = DatasetMetadata(
                    filename=filename,
                    domain=domain,
                    file_path=file_path,
                    row_count=len(cleaned_df),
                    column_count=len(cleaned_df.columns),
                    schema_info=schema_inference.column_mappings,
                    is_processed=True,
                )
                self.db.add(record)
                self.db.commit()
                self.db.refresh(record)
                dataset_id = record.id
            except Exception as exc:
                logger.warning(f"Failed to record dataset in database: {exc}")
                if self.db:
                    self.db.rollback()

        return {
            "dataset_id": dataset_id,
            "filename": filename,
            "domain": domain,
            "initial_rows": ingest_res.row_count,
            "cleaned_rows": len(cleaned_df),
            "columns": list(cleaned_df.columns),
            "schema_inference": schema_inference.column_mappings,
            "cleaning_notes": cleaning_report.notes,
        }
