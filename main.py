from pathlib import Path
import modules.audio_to_text
import modules.system_one
import modules.call_llm
import modules.api_calls
from time import perf_counter
import json
import os


def choix_fichier(audio_dir) -> str:
    fichiers = sorted(Path(audio_dir).glob("*.wav"))

    if not fichiers:
        raise FileNotFoundError(
            f"Aucun fichier .wav dans {audio_dir}, ajoutez d'abord un fichier d'audio."
        )

    for i, f in enumerate(fichiers, start=1):
        print(f"{i}. {f.name}")

    while True:
        choix = input("Numéro du fichier : ")
        if choix.isdigit() and 1 <= int(choix) <= len(fichiers):
            return str(fichiers[int(choix) - 1])
        print(f"Entre un nombre entre 1 et {len(fichiers)}.")


def main():
    # Transformation des fichiers en .wav (si besoin)
    modules.audio_to_text.convert_to_wav("res/")

    # Choix du fichier dans le dossier
    file = choix_fichier("res/")

    # Transcription du fichier .wav choisi
    transcribed_text = modules.audio_to_text.transcribe_audio(file)
    print("Audio transcrit:", transcribed_text)

    # System-One
    is_circulation = modules.system_one.is_circulation(transcribed_text)
    print("Jev prédit: c'est circulation ? ", is_circulation)

    if is_circulation < 0.5:
        print("Comme ce n'est pas de la circulation, on s'arrête ici.")
        return

    # Call LLM avec le texte
    start_llm = perf_counter()
    llm_data = modules.call_llm.extract_structured_data_llm(transcribed_text) or ""
    llm_perf = perf_counter() - start_llm
    print(f"Données extraites par le LLM (en {round(llm_perf,2)} s):", llm_data)
    if llm_data == "":
        print("LLM n'a rien donné, fin.")
        return

    llm_data_json = json.JSONDecoder().decode(llm_data)

    if not llm_data_json["city"]:
        print("Pas de nom de ville trouvé, on ne peut pas continuer.")
        return

    # A partir de la ville, on peut extraire les informations pour le modèle de prédiction
    weather_data = modules.api_calls.get_weather_data_by_city(llm_data_json["city"])

    print("Données reçues à partir de la météo:", weather_data)


if __name__ == "__main__":
    main()
