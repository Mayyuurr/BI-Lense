"""Data Ingestion Connectors.

Defines abstraction interfaces for reading raw SME data from ERP/CRM flat files
or direct database extracts.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import pandas as pd


@dataclass
class IngestionResult:
    """Metadata and DataFrame payload returned from data ingestion."""

    source_name: str
    domain: str
    dataframe: pd.DataFrame
    row_count: int
    column_count: int
    metadata: Dict[str, Any]


class BaseDataConnector(ABC):
    """Abstract base connector for data sources."""

    @abstractmethod
    def ingest(self, source_path_or_uri: str, **kwargs: Any) -> IngestionResult:
        """Ingests raw data and returns a structured IngestionResult.

        Args:
            source_path_or_uri: Local file path or database URI.
            **kwargs: Extra parameters (delimiter, sheet_name, etc.).

        Returns:
            IngestionResult containing dataframe and metadata.
        """
        pass


class CSVConnector(BaseDataConnector):
    """Connector for CSV / TSV tabular files."""

    def ingest(self, source_path_or_uri: str, domain: str = "general", **kwargs: Any) -> IngestionResult:
        """Reads a CSV file into a pandas DataFrame."""
        df = pd.read_csv(source_path_or_uri, **kwargs)
        return IngestionResult(
            source_name=source_path_or_uri,
            domain=domain,
            dataframe=df,
            row_count=len(df),
            column_count=len(df.columns),
            metadata={"columns": list(df.columns)},
        )


class DatabaseConnector(BaseDataConnector):
    """Connector for external SQL databases (ERP/CRM DBs)."""

    def ingest(self, source_path_or_uri: str, domain: str = "general", query: Optional[str] = None, **kwargs: Any) -> IngestionResult:
        """Reads records from an external database using a SQL query."""
        if not query:
            raise ValueError("Query string must be provided for DatabaseConnector.")
        # Placeholder interface for SQL ingestion
        df = pd.read_sql(query, con=source_path_or_uri, **kwargs)
        return IngestionResult(
            source_name="database_query",
            domain=domain,
            dataframe=df,
            row_count=len(df),
            column_count=len(df.columns),
            metadata={"query": query},
        )
