# sos-routier
SOS Routier helps emergency call handlers estimate the severity of a road accident. 
It takes in the caller's unstructured description, road conditions and other context, and turns them into structured data and a severity prediction, so the right resources are dispatched faster.

> ⚠️ **Decision-support tool only.** 
> Every output is a suggestion for the  human operator, who stays responsible for the final decision. 
> Addresses inferred by the LLM are flagged and must be confirmed with the caller.

## Getting started

### Prerequisites
- Python 3
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
The whole pipeline is available at `main.py`.
- Install dependencies with `uv`:
```bash
uv sync
```
- Add audio files to `res/`
- Launch pipeline:
```bash
uv run main.py
```

## Pipeline
#TODO

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
- Open-Meteo (`get_weather_data_by_city` in `api_calls.py`)
Gets weather data in specific city and converts that data to something the prediction model can use.

## Team
#TODO
