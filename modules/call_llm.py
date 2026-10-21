from dotenv import load_dotenv
from ollama import Client
import modules.llm_tool_utils
from pydantic import BaseModel
import inspect
from typing import get_type_hints
import os
import json

load_dotenv()  # Load environment variables from .env file

client = Client(headers={"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"})

MODEL = "gpt-oss:120b-cloud"
MAX_TOOL_ROUNDS = 6


### TOOLS
def web_search(query: str) -> str:
    """Search the web for a query and return the content of the first result."""
    result = client.web_search(query)
    return result.model_dump_json()


def web_fetch(url: str) -> str:
    """Fetch the content of a web page given its URL."""
    result = client.web_fetch(url)
    return result.model_dump_json()


AVAILABLE_TOOLS = {"web_search": web_search, "web_fetch": web_fetch}

tools_schema = [
    modules.llm_tool_utils.tool_schema(fn) for fn in AVAILABLE_TOOLS.values()
]


### LLM CALL
class LocationData(BaseModel):
    city: str | None
    postal_code: str | None
    road: str | None
    road_number: str | None
    road_type: str | None
    landmark: (
        str | None
    )  # point de repère cité par l'appelant (école, hôpital, gare, bâtiment public...)
    inferred: (
        bool | None
    )  # true si l'adresse a été déduite par le LLM donc à prendre avec précaution


SYSTEM_PROMPT = """\
<task>Extraire les informations de localisation d'un appel d'urgence.</task>

<rules>
- Remplis tous les champs qui sont mentionnés OU déductibles avec certitude.
- Si l'appelant cite un lieu connu (école, hôpital, gare, bâtiment public...),
  complète l'adresse officielle de ce lieu (rue, numéro, code postal, ville)
  et mets "inferred" à true.
- Si tu n'es pas sûr de l'adresse, mets null. N'invente jamais. Si tu n'as rien ajouté aux informations du texte fourni, mets inferred à false. Inferred est à true uniquement quand tu ajoutes des informations.
- Garde le lieu cité dans "landmark".
- road_type = type de voie en minuscules (rue, chemin, route, avenue, boulevard...).
  road = nom de la voie sans son type.
- Si tu ne peux pas déduire les informations avec certitude, laisse les champs vides (null).
- Il faut ABSOLUMENT répondre avec un JSON valide, sans texte supplémentaire.
</rules>

<example>
Entrée : "Accident devant la HEI à Sion"
Sortie : {"city": "Sion", "postal_code": "1950", "road": "rue de l'Industrie",
"road_number": "23", "road_type": "rue", "landmark": "HEI", "inferred": true}
</example>
"""

SEARCH_PROMPT = """\
<task>Tu aides à localiser précisément l'appelant d'un appel d'urgence.</task>
<rules>
- Si l'appelant cite un point de repère (commerce, école, hôpital, gare...),
  utilise l'outil web_search pour trouver son adresse officielle.
- Si plusieurs établissements correspondent (ex. plusieurs McDonald's dans la ville),
  note-les tous, ne choisis pas au hasard.
- N'invente jamais d'adresse.
- Quand tu as assez d'informations (ou que la recherche ne donne rien), réponds
  simplement par un court résumé de ce que tu as trouvé.
- Cherche avec le nom du lieu + la ville citée (ex. "McDonald's Sion adresse").
  Ne retiens que les résultats situés dans cette ville.
- Les appels ne concernent que la Suisse, donc si on te donne une ville en dehors, soit tu ne trouves pas la ville, soit tu trouves une ville qui correspond à peu près.
</rules>
"""


def run_tool(call) -> str:
    tool_name = call.function.name
    tool_args = call.function.arguments

    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"Tool {tool_name} is not available.")

    tool_fn = AVAILABLE_TOOLS[tool_name]
    result = tool_fn(**tool_args)
    return result


def research_phase(provided_data: str) -> str:
    messages = [
        {"role": "system", "content": SEARCH_PROMPT},
        {"role": "user", "content": f"<provided_data>{provided_data}</provided_data>"},
    ]
    summary = ""
    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat(model=MODEL, messages=messages, tools=tools_schema)
        messages.append(response.message)
        if not response.message.tool_calls:
            summary = response.message.content or ""
            break
        for call in response.message.tool_calls:
            result = run_tool(call)
            messages.append(
                {"role": "tool", "name": call.function.name, "content": result}
            )
    return summary


def extract_structured_data_llm(provided_data: str) -> str | None:
    research = research_phase(provided_data)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"<provided_data>{provided_data}</provided_data>\n"
                f"<research_results>{research}</research_results>"
            ),
        },
    ]

    response = client.chat(
        model=MODEL,
        messages=messages,
        stream=False,
        think="low",
        format=LocationData.model_json_schema(),
        options={
            "temperature": 0.0
        },  # le LLM utilisera uniquement les données à disposition pour éviter de halluciner d'autres
    )
    return response.message.content


### MAIN

if __name__ == "__main__":
    provided_data = "Bonjour à l'aide il y a un motard qui est tombé, on est à côté du macdo de Sion, il est inconscient"
    structured_data = extract_structured_data_llm(provided_data)
    print(structured_data)
