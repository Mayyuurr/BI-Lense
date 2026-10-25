import pandas as pd
from sqlalchemy import create_engine

from app.core.database import SessionLocal, engine
from app.models.Predicted_Cutomer_Will_But_Or_Not import Predicte_Customer_Will_Buy_Or_Not


def upload_csv(file):

    df = pd.read_csv(file.file)

    db = SessionLocal()

    try:

        for _, row in df.iterrows():

            customer = Predicte_Customer_Will_Buy_Or_Not(
                previous_purchases=int(row["previous_purchases"]),
                previous_visits=int(row["previous_visits"]),
                avg_time=float(row["avg_time"]),
                avg_pages=int(row["avg_pages"])
            )

            db.add(customer)

        db.commit()

        return len(df)

    finally:
        db.close()