"""Deterministic Data Cleaning and Normalization Module.

Provides deterministic cleaning interfaces for missing value handling,
deduplication, date parsing, and type coercion.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class CleaningReport:
    """Audit summary of modifications performed during data cleaning."""

    initial_rows: int
    final_rows: int
    dropped_duplicates: int
    filled_missing_values: Dict[str, int]
    coerced_types: Dict[str, str]
    notes: List[str]


class BaseDataCleaner(ABC):
    """Abstract base cleaner for tabular dataset processing."""

    @abstractmethod
    def clean(self, df: pd.DataFrame, schema_mapping: Optional[Dict[str, str]] = None) -> (pd.DataFrame, CleaningReport):
        """Cleans input DataFrame and returns cleaned DataFrame with audit report."""
        pass


class DeterministicDataCleaner(BaseDataCleaner):
    """Rule-based, deterministic data cleaner for SME datasets."""

    def clean(
        self,
        df: pd.DataFrame,
        schema_mapping: Optional[Dict[str, str]] = None,
    ) -> (pd.DataFrame, CleaningReport):
        """Applies deterministic cleaning rules:
        - Drops exact duplicate rows
        - Strips string whitespace
        - Standardizes column names (lowercase, snake_case)
        - Applies optional schema column mappings
        """
        initial_rows = len(df)
        cleaned_df = df.copy()

        # Standardize column naming
        cleaned_df.columns = [
            c.strip().lower().replace(" ", "_").replace("-", "_")
            for c in cleaned_df.columns
        ]

        if schema_mapping:
            cleaned_df = cleaned_df.rename(columns=schema_mapping)

        # Deduplication
        cleaned_df = cleaned_df.drop_duplicates()
        dropped_duplicates = initial_rows - len(cleaned_df)

        # Strip whitespace from text columns
        for col in cleaned_df.select_dtypes(include=["object"]).columns:
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip()

        report = CleaningReport(
            initial_rows=initial_rows,
            final_rows=len(cleaned_df),
            dropped_duplicates=dropped_duplicates,
            filled_missing_values={},
            coerced_types={},
            notes=["Standardized column names and removed duplicate rows."],
        )

        return cleaned_df, report
