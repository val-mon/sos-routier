import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.model_utils import export_model_data_json, get_auc_roc
from modules.system_one import predict_accident_gravity_with_features
from models.preprocess import get_data
import json


def get_jev_auc_and_roc() -> tuple[float, tuple[list[float], list[float]]]:
    """
    Récupère les valeurs AUC et ROC du modèle JEV à partir d'un fichier JSON.

    Returns:
        tuple: Un tuple contenant la valeur AUC (float) et la liste des valeurs ROC (tuple[list[float], list[float]]).
    """
    data = get_data(file="data/accidents.shz", drop_hour=False)

    # Obtenir probabilités d'échantillons aléatoires
    sample_data = data.sample(n=100, random_state=42)

    # pour meteo et etat_route, les valeurs sont en one_hot donc plusieurs colonnes pour chaque catégorie, on doit donc les transformer en une seule valeur pour chaque ligne
    sample_data["METEO"] = (
        sample_data[
            [
                "METEO_beau",
                "METEO_couvert",
                "METEO_chute de neige",
                "METEO_grêle",
                "METEO_pluie",
                "METEO_pluie givrante",
            ]
        ]
        .idxmax(axis=1)
        .apply(lambda x: x.split("_")[1])
    )
    sample_data["ETAT_ROUTE"] = (
        sample_data[
            [
                "ETAT_ROUTE_humide",
                "ETAT_ROUTE_mouillé",
                "ETAT_ROUTE_route enneigée",
                "ETAT_ROUTE_sèche",
                "ETAT_ROUTE_verglacée",
            ]
        ]
        .idxmax(axis=1)
        .apply(lambda x: x.split("_")[1])
    )

    probabilities = []

    for i, (_, row) in enumerate(sample_data.iterrows()):
        probabilities.append(
            predict_accident_gravity_with_features(
                row["HEURE"], row["METEO"], row["ETAT_ROUTE"], row["VITESSE_MA"]
            )
        )
        if i % 10 == 0:
            print(f"[JEV] Processed {i} samples...")

    return get_auc_roc(sample_data["VICTIME"], probabilities)


if __name__ == "__main__":
    auc, roc = get_jev_auc_and_roc()
    print(f"AUC: {auc}")
    print(f"ROC: {roc}")

    export_model_data_json("jev", auc, roc)
