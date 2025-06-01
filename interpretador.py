import os
from google import genai
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY =  os.environ.get("GOOGLE_TOKEN")
client = genai.Client(api_key=GEMINI_API_KEY)

with open("CoffeMaster\data\InstrucoesMestre.md", "r", encoding="utf-8") as f:
    instrucoes = f.read()


def fazer_pergunta(pergunta):
    resposta = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[instrucoes,pergunta]
    )
    return resposta.text



