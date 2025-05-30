
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

dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



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

arquivos = [livroJogador, monstros]
nomes = ["LivroJogador.md", "Monstros.md"]  
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
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

vectorstore = create_vectorsstore(documentos)
print(vectorstore.similarity_search("ataque"))
vectorstore.save_local("vector_db")