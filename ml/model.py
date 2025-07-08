import pandas as pd
from datetime import datetime
import os
import pickle

# Load trained model and encoders from ml_cache only once
MODEL_PATH = "ml/ml_cache/iforest_model.pkl"
EVENT_ENCODER_PATH = "ml/ml_cache/event_encoder.pkl"

model = None
endpoint_encoder = None
event_encoder = None


def load_model_and_encoders():
    global model, endpoint_encoder, event_encoder
    if model and endpoint_encoder and event_encoder:
        return model, endpoint_encoder, event_encoder

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(EVENT_ENCODER_PATH, "rb") as f:
        event_encoder = pickle.load(f)

    return model, endpoint_encoder, event_encoder


def extract_features(logs, endpoint_encoder, event_encoder):
    rows = []
    for log in logs:
        ts = log.get("timestamp")
        try:
            hour = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").hour
        except:
            hour = 0

        event = log.get("event", "UNKNOWN_ACTIVITY")

        event_enc = event_encoder.transform([event])[0] if event in event_encoder.classes_ else -1

        rows.append({
            "hour": hour,
            "event_encoded": event_enc
        })

    return pd.DataFrame(rows)

