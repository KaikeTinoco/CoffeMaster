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
import data_splitter
import CoffeMaster.interpretador as interpretador

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  
GEMINI_API_KEY =  os.environ.get("GOOGLE_TOKEN")
client = genai.Client(api_key=GEMINI_API_KEY)
bot = commands.Bot(command_prefix="!", intents=intents)
discord_token = os.getenv("DISCORD_TOKEN")
chat = client.chats.create(model="gemini-2.0-flash")


with open("CoffeMaster\data\instrucoes.md", "r", encoding="utf-8") as f:
    instrucoes = f.read()



canalDaCampanhaAtiva = {}

@bot.event
async def on_ready():
    print(f" Bot conectado como {bot.user}")

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
    prompt=f'''os jogadores iniciaram a campanha {nomeCampanha}, retome ela a partir do ultimo ponto de partida ou caso ela esteja vazia, inicie a campanha
    para identificar se a campanha está vazia, veja se o campo contextoNarrativoAtual, nos dados que você recebeu, está vazio. Se sim, a campanha ainda não iniciou. Se já estiver algo dentro
    do campo, a campanha já inicou. Com base nisso, seja bem descritivo e criativo para as duas situações, forneça uma introdução muito bem descritiva e interessante, ou uma continuação coerente
    com o que já aconteceu'''
    prompt_content = [instrucoes,
                      campanha_str, 
                      prompt]
    response = chat.send_message(prompt_content)
    for part in split_message(response.text):
        await ctx.send(part)



@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    canal = message.channel.id

    if canal in canalDaCampanhaAtiva and canalDaCampanhaAtiva[canal]["ativa"]:
        historico = canalDaCampanhaAtiva[canal]["historico"]
        historico.append({"usuario": message.author.name, "mensagem": message.content})

    response = gerarResposta(message.content)

    
    for part in split_message(response):
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



def gerarResposta(acao):
    pergunta = interpretador.fazer_pergunta(acao)
    resposta = data_splitter.gerarResposta(pergunta)
    conteudos = [resposta, acao]
    respostaFinal = chat.send_message(conteudos)
    return respostaFinal.text




def split_message(text, limit=2000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]




bot.run(discord_token)

