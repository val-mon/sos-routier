"""Pipeline séquentiel pour SOS Routier, avec résultats intermédiaires. Utilisé pour la page HTML"""

import json
from pathlib import Path
from time import perf_counter
from typing import Generator

import modules.audio_to_text as audio_to_text
import modules.system_one as system_one
import modules.call_llm as call_llm
import modules.api_calls as api_calls


def list_audio_files(audio_dir: str = "res/") -> list[str]:
    """Retourne la liste des fichiers .wav disponibles."""
    audio_to_text.convert_to_wav(audio_dir)
    return sorted([f.name for f in Path(audio_dir).glob("*.wav")])


def run_pipeline(filename: str, audio_dir: str = "res/") -> Generator[dict, None, None]:
    """
    Exécute le pipeline complet et yield un dict par étape.

    Chaque dict contient :
      - step: str          (nom de l'étape)
      - status: str        ("running" | "done" | "skipped" | "error")
      - data: dict | None  (résultat de l'étape)
      - duration: float    (durée en secondes, si terminée)
    """
    filepath = str(Path(audio_dir) / filename)

    # ── Étape 1 : Transcription ──
    yield {"step": "transcription", "status": "running", "data": None}
    t0 = perf_counter()
    try:
        transcript = audio_to_text.transcribe_audio(filepath)
    except Exception as e:
        yield {
            "step": "transcription",
            "status": "error",
            "data": {"error": str(e)},
            "duration": round(perf_counter() - t0, 2),
        }
        return
    yield {
        "step": "transcription",
        "status": "done",
        "data": {"text": transcript},
        "duration": round(perf_counter() - t0, 2),
    }

    # ── Étape 2 : Classification (System-One / Jev) ──
    yield {"step": "classification", "status": "running", "data": None}
    t0 = perf_counter()
    try:
        score, max_speed = system_one.analyse(transcript)
    except Exception as e:
        yield {
            "step": "classification",
            "status": "error",
            "data": {"error": str(e)},
            "duration": round(perf_counter() - t0, 2),
        }
        return
    is_circ = score >= 0.5
    yield {
        "step": "classification",
        "status": "done",
        "data": [
            {
                "score": round(score, 4),
                "is_circulation": is_circ,
            },
            max_speed,
        ],
        "duration": round(perf_counter() - t0, 2),
    }

    if not is_circ:
        yield {
            "step": "llm_extraction",
            "status": "skipped",
            "data": {"reason": "Pas un accident de circulation (score < 0.5)"},
        }
        yield {
            "step": "weather",
            "status": "skipped",
            "data": {"reason": "Pipeline arrêté après classification"},
        }
        return

    # ── Étape 3 : Extraction LLM ──
    yield {"step": "llm_extraction", "status": "running", "data": None}
    t0 = perf_counter()
    try:
        llm_raw = call_llm.extract_structured_data_llm(transcript) or ""
        if not llm_raw:
            yield {
                "step": "llm_extraction",
                "status": "error",
                "data": {"error": "Le LLM n'a rien retourné"},
                "duration": round(perf_counter() - t0, 2),
            }
            return
        llm_data = json.loads(llm_raw)
    except Exception as e:
        yield {
            "step": "llm_extraction",
            "status": "error",
            "data": {"error": str(e)},
            "duration": round(perf_counter() - t0, 2),
        }
        return
    yield {
        "step": "llm_extraction",
        "status": "done",
        "data": llm_data,
        "duration": round(perf_counter() - t0, 2),
    }

    # ── Étape 4 : Météo & conditions routières ──
    city = llm_data.get("city")
    if not city:
        yield {
            "step": "weather",
            "status": "skipped",
            "data": {"reason": "Pas de ville trouvée par le LLM"},
        }
        return

    yield {"step": "weather", "status": "running", "data": None}
    t0 = perf_counter()
    try:
        weather = api_calls.get_weather_data_by_city(city)
    except Exception as e:
        yield {
            "step": "weather",
            "status": "error",
            "data": {"error": str(e)},
            "duration": round(perf_counter() - t0, 2),
        }
        return
    yield {
        "step": "weather",
        "status": "done",
        "data": weather,
        "duration": round(perf_counter() - t0, 2),
    }


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
            return str(fichiers[int(choix) - 1].name)
        print(f"Entre un nombre entre 1 et {len(fichiers)}.")


if __name__ == "__main__":
    audio_to_text.convert_to_wav("res/")

    # Choix du fichier dans le dossier
    file = choix_fichier("res/")

    for b in run_pipeline(file):
        done = b["status"] == "done"
        if done:
            data = b["data"] or {}
            duration = f"[{b["duration"] or 0}s]"
        match b["step"]:
            case "transcription":
                if done:
                    print(duration, "Texte transcrit:\n\t", data["text"])
            case "classification":
                if done:
                    data_is_circ = data[0]
                    data_max_speed = data[1]
                    print(
                        duration,
                        "Classification de Jev:\n\tScore =",
                        data_is_circ["score"],
                        "=> is_circulation = ",
                        data_is_circ["is_circulation"],
                        "\n\tPredicted max speed =",
                        data_max_speed,
                        "km/h",
                    )
            case "llm_extraction":
                if done:
                    if data == {}:
                        print(
                            duration,
                            "Aucune donnée extraite par le LLM. Pas de continuation possible.",
                        )
                        break

                    print(duration, "Données extraites par le LLM:\n\t", data)
            case "weather":
                if done:
                    print(duration, "Données météo et état de la route:\n\t", data)
