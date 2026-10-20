# src: https://docs.typesafe.ai/introduction/quickstart

import os

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient

load_dotenv()

client = TypeSafeClient(model="jev-latest", api_key=os.getenv("TYPESAFE_API_KEY"))

def is_circulation(txt : str):
    response = client.system_one(
        state=txt,
        questions={
            "is_circulation": Noul(
                instructions="Lis les données suivantes et dis moi si ça concerne la circulation routière ou non",
            ),
        },
    )
    return response.nouls["is_circulation"].noul

if __name__ == "__main__":
    textes = [
        "Venez m'aider, mon chat et tombé de 4e étage",
        "Un motard vient de faire un accident, amenez les secours si vous êtes des tigres",
    ]

    for txt in textes:
        print(is_circulation(txt))
