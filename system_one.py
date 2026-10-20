# src: https://docs.typesafe.ai/introduction/quickstart

import os

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient

load_dotenv()

client = TypeSafeClient(model="jev-latest", api_key=os.getenv("TYPESAFE_API_KEY"))

PROMPT = """
<task>
Classify whether the provided emergency text concerns road traffic.
</task>

<context>
The text may be written in French or another language.
It can contain spelling or transcription errors.
Judge its meaning, not its wording.
</context>
"""


def is_circulation(txt: str) -> float:
    response = client.system_one(
        state=txt,
        questions={
            "is_circulation": Noul(
                instructions=PROMPT,
            ),
        },
    )
    return response.nouls["is_circulation"].noul
