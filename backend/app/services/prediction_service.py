import pandas as pd

from app.ml.customer.predictor import (
    train_model,
    predict_customers as model_predict_customer
)
from app.core.database import SessionLocal
from app.models.Predicted_Cutomer_Will_But_Or_Not import Predicte_Customer_Will_Buy_Or_Not


def train_customer_model(file):

    rows = train_model(file)

    return {
        "message": "Customer model trained successfully",
        "rows_used": rows
    }


def predict_customer():

    db = SessionLocal()

    try:

        customers = db.query(
            Predicte_Customer_Will_Buy_Or_Not
        ).filter(
            Predicte_Customer_Will_Buy_Or_Not.prediction.is_(None)
        ).all()

        if not customers:
            return {
                "message": "No customers available for prediction",
                "rows_predicted": 0
            }

        # Convert database rows to DataFrame
        data = pd.DataFrame([
            {
                "previous_purchases": customer.previous_purchases,
                "previous_visits": customer.previous_visits,
                "avg_time": customer.avg_time,
                "avg_pages": customer.avg_pages
            }
            for customer in customers
        ])

        # Send DataFrame to ML model
        predictions, probabilities = model_predict_customer(data)

        # Update database
        for customer, prediction, probability in zip(
            customers,
            predictions,
            probabilities
        ):
            customer.prediction = int(prediction)
            customer.probability = float(probability)

        db.commit()

        return {
            "message": "Prediction completed successfully",
            "rows_predicted": len(customers)
        }

    finally:
        db.close()