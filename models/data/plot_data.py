def plot_model_roc(model_data: dict):
    """
    Trace la courbe ROC du modèle à partir des données fournies.

    Args:
        model_data (dict): Dictionnaire contenant les données du modèle, y compris les valeurs AUC et ROC.
    """
    import matplotlib.pyplot as plt

    auc = model_data["AUC"]
    fpr, tpr = model_data["ROC"]

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color="blue", label=f"ROC curve (AUC = {auc:.2f})")
    plt.plot([0, 1], [0, 1], color="red", linestyle="--", label="Random guess")
    plt.xlim((0.0, 1.05))
    plt.ylim((0.0, 1.05))
    plt.xlabel("False Positive Rate", fontsize=36)
    plt.ylabel("True Positive Rate", fontsize=36)
    plt.title("ROC Curve for {} model".format(model_data["model_name"]), fontsize=36)
    plt.xticks(fontsize=26)
    plt.yticks(fontsize=26)
    plt.legend(fontsize=26)
    plt.grid()
    plt.show()


if __name__ == "__main__":
    import json
    import os
    from pathlib import Path

    for file in os.scandir("models/data"):
        path_file = Path(file.path)
        if path_file.suffix.lower() == ".json":
            with open(path_file, "r") as f:
                model_data = json.load(f)
            plot_model_roc(model_data)
