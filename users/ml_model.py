import pandas as pd
import joblib

from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from .models import UserBehavior


# =============================
# STEP A → Get dataset from DB
# =============================

def create_dataset(user_id):

    logs = UserBehavior.objects.filter(
        user_id=user_id
    ).order_by("timestamp")

    rows = []
    prev = None

    for log in logs:

        if prev:
            rows.append({
                "current": prev,
                "next": log.action
            })

        prev = log.action

    df = pd.DataFrame(rows)

    return df


# =============================
# STEP B → Train model (XGBoost)
# =============================

import os
import numpy as np


def train_model(user_id):

    logs = UserBehavior.objects.filter(
        user_id=user_id
    ).order_by("timestamp")

    actions = [l.action for l in logs if l.action != "logout"]

    if len(actions) < 4:
        return None

    unique = list(set(actions))
    mapping = {a: i for i, a in enumerate(unique)}

    X = []
    y = []

    for i in range(2, len(actions) - 1):
        X.append([
            mapping[actions[i-2]],
            mapping[actions[i-1]],
            mapping[actions[i]]
        ])
        y.append(mapping[actions[i + 1]])

    X = np.array(X)
    y = np.array(y)

    # XGBoost needs labels 0..k-1 with no gaps
    le = LabelEncoder()
    y = le.fit_transform(y)

    # only one possible next action -> nothing to learn
    if len(le.classes_) < 2:
        return None

    model = XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        random_state=42
    )
    model.fit(X, y)

    joblib.dump((model, mapping, le), f"model_user_{user_id}.pkl")

    return model, mapping, le



def predict_next(user_id, last_action):

    result = train_model(user_id)

    if result is None:
        return "Unknown", 0

    model, mapping, le = result

    logs = UserBehavior.objects.filter(
        user_id=user_id
    ).order_by("timestamp")

    actions = [l.action for l in logs if l.action != "logout"]

    if len(actions) < 3:
        return "Unknown", 0

    last_three = actions[-3:]

    features = [[mapping[a] for a in last_three]]

    # model gives encoded label -> convert back to mapping index
    pred = le.inverse_transform(model.predict(features))[0]
    prob = float(model.predict_proba(features)[0].max())   # float32 -> plain float for the DB

    reverse = {v: k for k, v in mapping.items()}

    return reverse[pred], round(prob * 100, 2)