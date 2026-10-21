# src: https://docs.typesafe.ai/introduction/quickstart

import os

from dotenv import load_dotenv
from typesafe_sdk import Noul, Choice, TypeSafeClient

load_dotenv()

client = TypeSafeClient(model="jev-latest", api_key=os.getenv("TYPESAFE_API_KEY"))

CONTEXT = """
<context>
The text may be written in French or another language.
It can contain spelling or transcription errors.
Judge its meaning, not its wording.
</context>
"""


def analyse(txt: str):
    response = client.system_one(
        state=txt,
        questions={
            "is_circulation": Noul(
                instructions="""
                <task>
                Classify whether the provided emergency text concerns road traffic.
                </task>
                """ + CONTEXT,
            ),
            "road_max_speed": Choice(
                instructions="""
                <task>
                Classify the type of road mentioned in the provided emergency text based in it's maximum speed.
                </task>
                """ + CONTEXT,
                criteria={
                    "120": "Highway or motorway (~120 km/h)",
                    "80": "Cantonal road (~80 km/h)",
                    "50": "City road (~50 km/h)",
                    "30": "Urban road (~30 km/h)",
                },
            ),
        },
    )
    return (
        response.nouls["is_circulation"].noul,
        response.choices["road_max_speed"].choice,
    )
