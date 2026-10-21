# sos-routier
SOS Routier helps emergency call handlers estimate the severity of a road accident. 
It takes in the caller's unstructured description, road conditions and other context, and turns them into structured data and a severity prediction, so the right resources are dispatched faster.

> ⚠️ **Decision-support tool only.** 
> Every output is a suggestion for the  human operator, who stays responsible for the final decision. 
> Addresses inferred by the LLM are flagged and must be confirmed with the caller.

## Getting started

### Prerequisites
- Python 3.13+
- uv (https://docs.astral.sh/uv/)
- Ollama account and API key (https://ollama.com/settings/keys)
- Typesafe AI account with credits (less than a cent will be used) (https://console.typesafe.ai/home)

### Installation

```bash
git clone https://github.com/val-mon/sos-routier
cd sos-routier
uv sync
``` 

### Configuration
Create a `.env` file at the project root (see [.env.example](./.env.example) for formatting)
You'll need an Ollama API key (only free models are used) and a Typesafe AI API key (For System-One Jev)

### Usage

Add audio files (`.wav` or other formats) to the `res/` directory.

#### Web interface (recommended)
```bash
uv run server.py
```
Open http://localhost:8000 in your browser. Select an audio file and click **▶ Lancer** to run the full pipeline with real-time results.

#### CLI
```bash
uv run main.py
```
Follow the prompts to select a file and see the results in the terminal.

## Pipeline

```
Audio (.wav) ──► Transcription ──► Classification ──► Extraction LLM ──► Conditions routières
                  (MOSS)            (Jev)              (Ollama)           (Open-Meteo)
```

### Audio to text
Transcription of audio files using the [MOSS-Transcribe-Diarize](https://huggingface.co/OpenMOSS-Team/MOSS-Transcribe-Diarize) model from HuggingFace. Supports speaker diarization. Non-`.wav` files in `res/` are automatically converted before transcription.

### System-One (Jev)
Binary classification using [Typesafe AI](https://typesafe.ai/)'s System-One model (`jev-latest`) to determine whether the transcribed call concerns a **road traffic incident** (score ≥ 0.5). If not, the pipeline stops early.

### Call LLM
First iteration of the call LLM file uses a free-tier LLM from [Ollama](https://ollama.com/) (currently: `gpt-oss:120b-cloud`) to take the transcript from the emergency call and extract location from it.
The output of the `extract_structured_data_llm()` function is a JSON in `str` data type in the format:
```json
{
    "city": "Sion",
    "postal_code": "1950",
    "road": "de la Gare",
    "road_number": "3",
    "road_type": "avenue",
    "landmark": "McDonald's",
    "inferred": true
}
```

For this to work, you'll need to add your Ollama API key in `.env`. Check formatting in the [.env.example](./.env.example) file.

### API calls
- **Open-Meteo** (`get_weather_data_by_city` in `api_calls.py`) — gets current weather for the extracted city and converts it into features for the prediction model: `METEO`, `ETAT ROUTE`, `LUMIERE`.
- **Ollama web tools** (`web_search`, `web_fetch` in `call_llm.py`) — used by the LLM during the research phase to look up addresses of landmarks mentioned by the caller.

## Team
- Valentin Monod - https://github.com/val-mon
- Gaëtan Veuillet - https://github.com/Dyumes
- Gonçalo Arieira Esteves - https://github.com/g-ae

---
*Parts of this README were drafted with the help of an AI assistant.*
