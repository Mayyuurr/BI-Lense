from fastapi import APIRouter, File, UploadFile

from pydantic import BaseModel

from app.services import prediction_service

router = APIRouter()

@router.post("/train_customer_will_buy_or_not")
def train_customer_model(
    file: UploadFile = File(...)
) -> dict:

    return prediction_service.train_customer_model(file)

@router.post("/predict_customer_will_buy_or_not")
def predict_customer() -> dict:

    return prediction_service.predict_customer()