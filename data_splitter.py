
from langchain.text_splitter import RecursiveCharacterTextSplitter

with open("CoffeMaster\data\LivroJogador.md", "r", encoding="utf-8") as f:
    livroJogador = f.read()


splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
)

def dividir_texto(documento):
    return splitter.split_text(documento)


resultado = dividir_texto(livroJogador)
with open("chunks_output.txt", "w", encoding="utf-8") as f:
    for chunk in resultado:
        f.write(chunk + "\n" + "-"*80 + "\n")

