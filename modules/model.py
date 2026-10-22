"""Prédiction de présence de victimes avec le Random Forest exporté."""

import math
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "random_forest_model.pkl"

# Colonnes exactes vues à l'entraînement (sans VICTIME, qui est la cible)
FEATURE_COLUMNS = [
    "VITESSE_MA",
    "METEO_beau",
    "METEO_chute de neige",
    "METEO_couvert",
    "METEO_grêle",
    "METEO_pluie",
    "METEO_pluie givrante",
    "ETAT_ROUTE_enneigée",
    "ETAT_ROUTE_humide",
    "ETAT_ROUTE_mouillé",
    "ETAT_ROUTE_neige fondante",
    "ETAT_ROUTE_route enneigée",
    "ETAT_ROUTE_sèche",
    "ETAT_ROUTE_verglacée",
    "HEURE_SIN",
    "HEURE_COS",
]

METEO_VALUES = {c.removeprefix("METEO_") for c in FEATURE_COLUMNS if c.startswith("METEO_")}
ROUTE_VALUES = {c.removeprefix("ETAT_ROUTE_") for c in FEATURE_COLUMNS if c.startswith("ETAT_ROUTE_")}

# Valeurs renvoyées par l'API → valeurs connues du modèle
ROUTE_ALIASES = {"mouillée": "mouillé"}
METEO_ALIASES = {}


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Modèle introuvable : {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


def _to_py(v):
    return v.item() if isinstance(v, np.generic) else v


def _normalize(value: str, aliases: dict) -> str:
    v = str(value).strip().lower()
    return aliases.get(v, v)


def build_features(max_speed, weather: dict, hour: float | None = None):
    """Retourne (DataFrame d'une ligne pour le modèle, infos lisibles, avertissements)."""
    now = datetime.now()
    if hour is None:
        hour = now.hour

    meteo = _normalize(weather["METEO"], METEO_ALIASES)
    route = _normalize(weather["ETAT ROUTE"], ROUTE_ALIASES)

    warnings = []
    if meteo not in METEO_VALUES:
        warnings.append(f"Météo « {meteo} » inconnue du modèle (toutes colonnes METEO à 0)")
    if route not in ROUTE_VALUES:
        warnings.append(f"État route « {route} » inconnu du modèle (toutes colonnes ETAT_ROUTE à 0)")

    row = dict.fromkeys(FEATURE_COLUMNS, 0)
    row["VITESSE_MA"] = int(max_speed)
    row["HEURE_SIN"] = math.sin(2 * math.pi * hour / 24)
    row["HEURE_COS"] = math.cos(2 * math.pi * hour / 24)
    if f"METEO_{meteo}" in row:
        row[f"METEO_{meteo}"] = 1
    if f"ETAT_ROUTE_{route}" in row:
        row[f"ETAT_ROUTE_{route}"] = 1

    X = pd.DataFrame([row], columns=FEATURE_COLUMNS)

    inputs = {
        "Heure": now.strftime("%H:%M"),
        "Vitesse max": f"{int(max_speed)} km/h",
        "Météo": meteo,
        "État route": route,
    }
    return X, inputs, warnings


def predict(max_speed, weather: dict) -> dict:
    model = load_model()
    X, inputs, warnings = build_features(max_speed, weather)

    # Sécurité : même ordre de colonnes que le modèle, s'il le connaît
    expected = getattr(model, "feature_names_in_", None)
    if expected is not None:
        X = X.reindex(columns=list(expected), fill_value=0)

    pred = _to_py(model.predict(X)[0])
    result = {"prediction": pred, "inputs": inputs, "warnings": warnings}

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        result["probabilities"] = {
            str(_to_py(c)): round(float(p), 4) for c, p in zip(model.classes_, proba)
        }
        result["confidence"] = round(float(max(proba)), 4)

    return result