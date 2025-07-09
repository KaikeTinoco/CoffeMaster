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
from Bot_Gerador_de_Personagens import app as geradorPersonagem
from Bot_Gerador_de_História import main as geradorHistoria


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  
GEMINI_API_KEY =  os.environ.get("GOOGLE_TOKEN")
client = genai.Client(api_key=GEMINI_API_KEY)
bot = commands.Bot(command_prefix="!", intents=intents)
discord_token = os.getenv("DISCORD_TOKEN")


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
    chat = client.chats.create(model="gemini-2.0-flash")
    canalDaCampanhaAtiva[ctx.channel.id] = {
        "dadosCampanha": campanha,
        "ativa": True,
        "nome": nomeCampanha,
        "historico": [],
        "chat": chat
    }
    prompt = f"A partir dos dados enviados, inicie a campanha {nomeCampanha}"
    mensagem_formatada = f"{instrucoes}\n\n### DADOS DA CAMPANHA:\n{campanha_str}\n\n### AÇÃO:\n{prompt}"
    response = chat.send_message(mensagem_formatada)
    for part in split_message(response.text):
        await ctx.send(part)



@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.strip().startswith("!"):
        await bot.process_commands(message)
        return
    
    canal = message.channel.id

    if canal in canalDaCampanhaAtiva and canalDaCampanhaAtiva[canal]["ativa"]:
        historico = canalDaCampanhaAtiva[canal]["historico"]
        historico.append({"usuario": message.author.name, "mensagem": message.content})

    response = gerarResposta(message.content, message.channel.id)

    
    for part in split_message(response):
        await message.channel.send(part)


@bot.command()
async def criarPersonagem(ctx, *, descricao_completa:str):
    partes = descricao_completa.rsplit(';', 1)
    if len(partes) == 2:
        descricao = partes[0]
        try:
            campanhaId_str = partes[1].strip()
            campanhaId = int(campanhaId_str)
        except ValueError:
            await ctx.send("Formato inválido para o ID da campanha. Use: `!criarPersonagem <descrição>, <ID_campanha>`")
            return
    else:
        await ctx.send("Formato inválido. Use: `!criarPersonagem <descrição>; <ID_campanha>`")
        return
    print(descricao, campanhaId)
    personagem = geradorPersonagem.criarPersonagem(descricao)
    api_response = api_client.criarPersonagem(personagem, campanhaId)
    if hasattr(api_response, 'json') and callable(api_response.json):
        personagem_json = api_response.json()
    else:
        personagem_json = api_response
    response_str = json.dumps(personagem_json, indent=4, ensure_ascii=False)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[response_str, "retorne esse JSON de uma maneira lúdica para o usuário, seja sucinto e simples"]
    )
    for part in split_message(response.text):
        await ctx.send(part)    


@bot.command()
async def alterarFicha(ctx, *, descricao_completa):
    partes = descricao_completa.rsplit(';')
    if (len(partes) == 3):
        descricao = partes[0]
        personagemNome = partes[1].strip()
        campanhaNome = partes[2].strip()
    else:
        await ctx.send("Formato inválido. Use: `!alterarFicha <descrição>; <nome Do personagem>; <nome da Campanha>`")
        return
    api_response = geradorPersonagem.alterarFicha(descricao, personagemNome, campanhaNome)
    if hasattr(api_response, 'json') and callable(api_response.json):
        personagem_json = api_response.json()
    else:
        personagem_json = api_response
    response_str = json.dumps(personagem_json, indent=4, ensure_ascii=False)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[response_str, "retorne esse JSON de uma maneira lúdica para o usuário, seja sucinto e simples"]
    )
    for part in split_message(response.text):
        await ctx.send(part)    



@bot.command()
async def criarCampanha(ctx, *, descricao_campanha):
    campanhaJson = geradorHistoria.criarHistoria(descricao_campanha)
    api_response = api_client.criarCampanha(campanhaJson)
    if hasattr(api_response, 'json') and callable(api_response.json):
        campanha_json = api_response.json()
    else:
        campanha_json = api_response
    response_str = json.dumps(campanha_json, indent=4, ensure_ascii=False)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[response_str, "retorne esse JSON de uma maneira lúdica para o usuário, seja sucinto e simples. Fale como se você fosse um mestre de campanhas de DnD"]
    )
    for part in split_message(response.text):
        await ctx.send(part)  


@bot.command()
async def perguntar(ctx, *, pergunta):
    channel_id = ctx.channel.id
    dados = data_splitter.fazer_busca(pergunta)
    dados_str = "\n\n".join([doc.page_content for doc in dados])
    if channel_id in canalDaCampanhaAtiva:
        chat = canalDaCampanhaAtiva[channel_id]["chat"]
        conteudos = [dados_str, pergunta]
        resposta = chat.send_message(conteudos)
        for part in split_message(resposta.text):
            await ctx.send(part)
    else:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[dados_str, 
                      pergunta, 
                      "Você é um mestre de DnD 5e. Responda a pergunta do usuário com base nos dados e em seu conhecimento"]
        )
        for part in split_message(response.text):
            await ctx.send(part)





@bot.command()
async def encerrar(ctx):
    resumo_dto = {
        "nomeCampanha":"",
        "resumoSessao":""
    }
    canal_id = ctx.channel.id
    chat = canalDaCampanhaAtiva[canal_id]["chat"]
    json_string = json.dumps(resumo_dto, indent=2)
    conteudo = ["iremos encerrar a sessão por aqui, por favor, faça um resumo dessa sessão com o máximo de detalhes possíveis. Sua resposta deverá seguir o formato do seguinte JSON", 
                json_string ]
    if canal_id in canalDaCampanhaAtiva:
        resumo = chat.send_message(conteudo)
        print(api_client.atualizarCampanha(resumo.text))
        chat.delete()
        del canalDaCampanhaAtiva[canal_id]
        await ctx.send("⛔ Sessão encerrada.")
    else:
        await ctx.send("❌ Nenhuma sessão ativa neste canal.")



def gerarResposta(acao, id_canal):
    chat = canalDaCampanhaAtiva[id_canal]["chat"]
    pergunta = interpretador.fazer_pergunta(acao)
    dados = data_splitter.fazer_busca(pergunta)
    dados_text = "\n\n".join([doc.page_content for doc in dados])
    resposta = geradorHistoria.mestrar(acao, chat, dados_text)
    resposta_principal = processarJSonRespostaMestre(geradorHistoria.extrair_json_de_markdown(resposta))
    respostaFinal = chat.send_message(resposta_principal)
    return respostaFinal.text



def split_message(text, limit=2000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]


def processarJSonRespostaMestre(json_data):
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            print("Erro: A string fornecida não é um JSON válido.")
            return "", []
    elif isinstance(json_data, dict):
        data = json_data
    else:
        print("Erro: A entrada deve ser uma string JSON ou um dicionário.")
        return "", []

    resposta_principal = data.get("resposta", "")
    descricoes_npcs = []    
    for key, value in data.items():
        if key.startswith("descricaoNpc"):
            if isinstance(value, str):
                descricoes_npcs.append(value)
            else:
                descricoes_npcs.append(str(value)) 
    
    if(len(descricoes_npcs) > 0):
        for descricao in descricoes_npcs:
            criarNpc(descricao)

    return resposta_principal


def criarNpc(descricao):
    personagem = geradorPersonagem.criarPersonagem(descricao)
    response = api_client.criarPersonagem(personagem)
    print(f"Personagem criado: {response}")

    




bot.run(discord_token)

