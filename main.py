import discord
import os
import sys
from google import genai
from dotenv import load_dotenv
from discord.ext import commands
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api_client import api_client
import json


discord_token = os.getenv("DISCORD_TOKEN")

with open("CoffeMaster\data\instrucoes.md", "r", encoding="utf-8") as f:
    instrucoes = f.read()

with open("CoffeMaster\data\LivroJogador.md", "r", encoding="utf-8") as f:
    livroJogador = f.read()

with open("CoffeMaster\data\Monstros_formatado.md", "r", encoding="utf-8") as f:
    monstros = f.read()

with open("CoffeMaster\data\LivroMestre.md", "r", encoding="utf-8") as f:
    mestre1 = f.read()

with open("CoffeMaster\data\LivroMestre2.md", "r", encoding="utf-8") as f:
    mestre2 = f.read()

with open("CoffeMaster\data\LivroMestre3.md", "r", encoding="utf-8") as f:
    mestre3 = f.read()

with open("CoffeMaster\data\LivroMestre4.md", "r", encoding="utf-8") as f:
    mestre4 = f.read()    


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  
GEMINI_API_KEY =  os.environ.get("GOOGLE_TOKEN")
client = genai.Client(api_key=GEMINI_API_KEY)
chat = client.chats.create(model="gemini-2.0-flash")
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command()
async def buscarCampanha(ctx, nomeCampanha):
    campanha = api_client.buscarCampanhaPorNome(nomeCampanha)
    campanha_str = json.dumps(campanha, ensure_ascii=False, indent=2)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[instrucoes, campanha_str, "Com base nos arquivos e nos dados da campanha encontrada, descreva ela de uma maneira lúdica para os usuários"]
    )
    for part in split_message(response.text):
        await ctx.send(part)


def split_message(text, limit=2000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]




bot.run(discord_token)

#)
