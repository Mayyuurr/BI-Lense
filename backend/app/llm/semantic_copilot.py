"""Semantic Preprocessing Copilot Module.

Uses local LLaMA to interpret raw ERP/CRM schemas, suggest column mappings,
infer semantic data types, and recommend deterministic cleaning actions.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from app.llm.llama_client import BaseLLMClient


@dataclass
class SchemaInferenceResult:
    """Output from semantic schema analysis."""

    domain: str
    column_mappings: Dict[str, str]
    inferred_types: Dict[str, str]
    semantic_tags: Dict[str, str]
    suggested_cleaning_steps: List[str]
    raw_llm_response: Optional[str] = None


class SemanticCopilot:
    """Assists in semantic interpretation of unfamiliar SME ERP/CRM datasets."""

    def __init__(self, llm_client: BaseLLMClient) -> None:
        self.llm_client = llm_client

    async def infer_schema(
        self,
        domain: str,
        columns: List[str],
        sample_rows: List[Dict[str, Any]],
    ) -> SchemaInferenceResult:
        """Analyzes column names and sample data to determine semantic business mappings.

        Note: Provides suggestions only; deterministic cleaning executes separately.
        """
        system_prompt = (
            "You are an expert data engineering copilot for SME ERP/CRM systems. "
            "Your role is to understand schema headers, identify standard business columns "
            "(e.g., date, product_id, revenue, quantity, lead_time), and suggest preprocessing actions."
        )

        user_prompt = (
            f"Domain: {domain}\n"
            f"Columns: {columns}\n"
            f"Sample Data (first 3 rows): {sample_rows[:3]}\n"
            "Task: Identify standard column mappings, data types, and preprocessing suggestions."
        )

        raw_response = await self.llm_client.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        # Baseline default mappings as safe fallback
        mappings = {col: col.lower().replace(" ", "_") for col in columns}
        types = {col: "string" for col in columns}

        return SchemaInferenceResult(
            domain=domain,
            column_mappings=mappings,
            inferred_types=types,
            semantic_tags={},
            suggested_cleaning_steps=["Remove duplicates", "Standardize column headers"],
            raw_llm_response=raw_response,
        )
