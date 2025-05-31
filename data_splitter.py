
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.text_splitter import TextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import faiss
import os
import dotenv
from google import genai

dotenv.load_dotenv()

GEMINI_API_KEY =  os.environ.get("GOOGLE_TOKEN")
client = genai.Client(api_key=GEMINI_API_KEY)



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

arquivos = [livroJogador, monstros, mestre1, mestre2, mestre3, mestre4]
nomes = ["LivroJogador.md", "Monstros.md", "Mestre1.md", "Mestre2.md", "Mestre3.md", "Mestre4.md"]  
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=100,
    separators=["\n\n", "\n", "##","###",".", "!", "?", ","]
)

conteudos = []
metadatas = []


for arquivo, nome in zip(arquivos, nomes):
    chunks = splitter.split_text(arquivo)
    conteudos.extend(chunks)  
    metadatas.extend([{"source": nome}] * len(chunks))  

documentos = splitter.create_documents(conteudos, metadatas=metadatas)

for i, doc in enumerate(documentos):
    with open(f"CoffeMaster\data\chunks\datadocument_chunks_output{i}.txt", "w", encoding="utf-8") as f:
        f.write(f"--- Documento {i + 1} ---\n")
        f.write(f"Fonte: {doc.metadata.get('source', 'desconhecida')}\n")
        f.write(doc.page_content + "\n\n")

def create_vectorsstore(chunks):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore

#vectorstore = create_vectorsstore(documentos)
#vectorstore.save_local("CoffeMaster/faiss_db")
vectorstore = FAISS.load_local("CoffeMaster/faiss_db", HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"), allow_dangerous_deserialization=True)
#Transforma a vector store em um retriver
retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 7})

prompt = "Vocé é um bot especialista em RPG que ajuda a responder perguntas sobre Dungeons and Dragons, com base nos dados recebidos e seus conhecimentos, responda a pergunta do usuário."
def gerarResposta(pergunta):
    respostaRetriever = retriever.invoke(pergunta)
    resposta_texto = "\n\n".join([doc.page_content for doc in respostaRetriever])
    reposta = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt, resposta_texto, pergunta]
    )
    return reposta.text

teste = gerarResposta("Se eu estiver em uma sala escura, sendo um dragonborn, posso usar minha habilidade de cuspir fogo para iluminar a sala?")
print(teste)