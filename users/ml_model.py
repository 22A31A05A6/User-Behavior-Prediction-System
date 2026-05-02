import pandas as pd
import joblib

from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

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
# STEP B → Train model
# =============================

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from users.models import UserBehavior


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

    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)

    joblib.dump((model, mapping), f"model_user_{user_id}.pkl")

    return model, mapping



def predict_next(user_id, last_action):

    result = train_model(user_id)

    if result is None:
        return "Unknown", 0

    model, mapping = result

    logs = UserBehavior.objects.filter(
        user_id=user_id
    ).order_by("timestamp")

    actions = [l.action for l in logs if l.action != "logout"]

    if len(actions) < 3:
        return "Unknown", 0

    last_three = actions[-3:]

    features = [[mapping[a] for a in last_three]]

    pred = model.predict(features)[0]
    prob = model.predict_proba(features)[0].max()

    reverse = {v: k for k, v in mapping.items()}

    return reverse[pred], round(prob * 100, 2)
