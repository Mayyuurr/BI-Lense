"""Dataset Ingestion and Semantic Schema Analysis Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


class IngestRequest(BaseModel):
    """Payload for dataset ingestion trigger."""

    file_path: str
    domain: str
    filename: Optional[str] = None


class IngestResponse(BaseModel):
    """Response returned after ingestion and semantic schema check."""

    dataset_id: Optional[int] = None
    filename: str
    domain: str
    initial_rows: int
    cleaned_rows: int
    columns: List[str]
    schema_inference: Dict[str, str]
    cleaning_notes: List[str]


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_200_OK)
async def ingest_dataset(
    payload: IngestRequest,
    db: Session = Depends(get_db),
) -> IngestResponse:
    """Ingests raw ERP/CRM file, applies semantic copilot schema mapping, and deterministic cleaning."""
    try:
        service = DatasetService(db=db)
        result = await service.ingest_and_analyze(
            file_path=payload.file_path,
            domain=payload.domain,
            filename=payload.filename or payload.file_path.split("/")[-1],
        )
        return IngestResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
