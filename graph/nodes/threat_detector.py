from ml.model import load_model_and_encoders, extract_features


def threat_detector_agent(state):
    """
    ThreatDetectorAgent (Model-Based): Loads pre-trained Isolation Forest model and encoders
    from ml_cache to detect anomalous logs.

    Input:
    - state['logs']: List of raw logs

    Output:
    - state['logs']: Logs flagged as anomalous
    """
    logs = state.get("logs", [])
    if not logs:
        state["logs"] = []
        return state

    # Load model + encoders
    model, event_encoder = load_model_and_encoders()
    X = extract_features(logs, event_encoder)

    predictions = model.predict(X)  # -1 = anomaly
    suspicious = []
    for i, pred in enumerate(predictions):
        if pred == -1:
            suspicious.append({**logs[i]})

    state["logs"] = suspicious

    return state
