# sos-routier

## Pipeline

## Call LLM
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

Pour ce faire, il faudra ajouter votre clé API Ollama dans `.env`. Vous pouvez voir le format dans le `.env.example`.