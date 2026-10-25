from fastapi import APIRouter, UploadFile, File

from app.services  import dataset_service

router = APIRouter()


@router.post("/upload_csv_for_customer_will_buy_or_not_prediction")
def upload_csv_file(file: UploadFile = File(...))-> dict:

    rows = dataset_service.upload_csv(file)

    return {
        "message": "CSV uploaded successfully",
        "rows_inserted": rows
    }