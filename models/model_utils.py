import json
import pathlib


def export_model_data_json(
    model_name: str, AUC: float, ROC: tuple[list[float], list[float]]
) -> None:
    """
    Exporte les données du modèle dans un fichier JSON.

    Args:
        model_name (str): Nom du modèle.
        AUC (float): Valeur de l'AUC.
        ROC (tuple[list[float], list[float]]): Liste des valeurs du ROC ().
    """

    current_dir = pathlib.Path(__file__).resolve().parent

    data_dir = current_dir / "data"

    data_dir.mkdir(parents=True, exist_ok=True)

    file_path = data_dir / f"data_{model_name}.json"

    data = {
        "model_name": model_name,
        "AUC": AUC,
        "ROC": ROC,
    }
    with open(file_path, "w+") as f:
        json.dump(data, f, indent=4)

def get_auc_roc(
    y_true: list, probabilities: list
) -> tuple[float, tuple[list[float], list[float]]]:
    """
    Calcule les valeurs AUC et ROC à partir des étiquettes réelles et des probabilités prédites.

    Args:
        y_true (list): Liste des étiquettes réelles.
        probabilities (list): Liste des probabilités prédites.

    Returns:
        tuple: Un tuple contenant la valeur AUC (float) et la liste des valeurs ROC (tuple[list[float], list[float]]).
    """
    from sklearn.metrics import roc_auc_score, roc_curve

    auc = roc_auc_score(y_true, probabilities)
    fpr, tpr, thresholds = roc_curve(y_true, probabilities)

    return auc, (fpr.tolist(), tpr.tolist())
