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

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  
GEMINI_API_KEY =  os.environ.get("GOOGLE_TOKEN")
client = genai.Client(api_key=GEMINI_API_KEY)
bot = commands.Bot(command_prefix="!", intents=intents)
discord_token = os.getenv("DISCORD_TOKEN")
chat = client.chats.create(model="gemini-2.0-flash")
openAiApiKey = "lm-studio"


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


canalDaCampanhaAtiva = {}

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


@bot.command()
async def iniciar(ctx, nomeCampanha):
    campanha = api_client.buscarCampanhaPorNome(nomeCampanha)
    campanha_str = json.dumps(campanha, ensure_ascii=False, indent=2)
    canalDaCampanhaAtiva[ctx.channel.id] = {
        "dadosCampanha": campanha,
        "ativa": True,
        "nome": nomeCampanha,
        "historico": []
    }
    documentos = [instrucoes, mestre1, mestre2, mestre3, mestre4, livroJogador, monstros]
    await enviar_arquivos_com_delay(chat, documentos)
    response = chat.send_message(campanha_str, f"os jogadores iniciaram a campanha {nomeCampanha}, retome ela a partir do ultimo ponto de partida ou caso ela esteja vazia, inicie a campanha")
    await ctx.send(response.text)


import asyncio

async def enviar_arquivos_com_delay(chat, arquivos, delay=8):
    """
    Envia uma lista de arquivos (strings) para o chat Gemini com um delay entre cada envio.
    
    :param chat: instância do chat iniciada com google.generativeai.GenerativeModel(...)
    :param arquivos: lista de strings ou conteúdo .md já carregado
    :param delay: tempo em segundos entre cada envio (padrão: 8s)
    """
    for index, arquivo in enumerate(arquivos, 1):
        try:
            print(f"Enviando arquivo {index}/{len(arquivos)}...")
            await chat.send_message(arquivo)
            await asyncio.sleep(delay)
        except Exception as e:
            print(f"Erro ao enviar o arquivo {index}: {e}")



@bot.event
async def onMessage(message):
    if message.author.bot:
        return
    
    canal = message.channel.id

    if canal in canalDaCampanhaAtiva and canalDaCampanhaAtiva[canal]["ativa"]:
        historico = canalDaCampanhaAtiva[canal]["historico"]
        historico.append({"usuario": message.author.name, "mensagem": message.content})


    response = chat.send_message(f"o jogador {message.author.name} disse: {message.content}")
    
    for part in split_message(response.text):
        await message.channel.send(part)

    await bot.process_commands(message)


@bot.command()
async def encerrar(ctx):
    canal_id = ctx.channel.id
    if canal_id in canalDaCampanhaAtiva:
        del canalDaCampanhaAtiva[canal_id]
        await ctx.send("⛔ Campanha encerrada.")
    else:
        await ctx.send("❌ Nenhuma campanha ativa neste canal.")




def split_message(text, limit=2000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]




bot.run(discord_token)

