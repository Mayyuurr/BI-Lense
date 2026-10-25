import os
import joblib
import pandas as pd

from xgboost import XGBClassifier


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "customer_model.pkl"
)


FEATURES = [
    "previous_purchases",
    "previous_visits",
    "avg_time",
    "avg_pages"
]

TARGET = "purchased_next_visit"


def train_model(file):

    df = pd.read_csv(file.file)

    X = df[FEATURES]
    y = df[TARGET]

    model = XGBClassifier(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss"
    )

    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)

    return len(df)


def predict_customers(df):

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "Customer model has not been trained yet."
        )

    model = joblib.load(MODEL_PATH)

    X = df[FEATURES]

    predictions = model.predict(X)

    probabilities = model.predict_proba(X)[:, 1]

    return predictions, probabilities